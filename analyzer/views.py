from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import AnalyzedString
from .serializers import AnalyzedStringSerializer
from .utils import analyze_string
# 🔹 Combined Endpoint for /strings (GET + POST)
# 🔹 /strings — GET (list) + POST (create)
@api_view(['POST','GET'])

def strings(request):
    # --- POST: Create / Analyze string ---
    if request.method == 'POST':
        value = request.data.get("value")

        if value is None:
            return Response({"error": "Missing 'value' field"}, status=400)
        if not isinstance(value, str):
            return Response({"error": "'value' must be a string"}, status=422)

        analysis = analyze_string(value)
        if AnalyzedString.objects.filter(id=analysis["sha256_hash"]).exists():
            return Response({"error": "String already exists"}, status=409)

        obj = AnalyzedString.objects.create(
            id=analysis["sha256_hash"],
            value=value,
            **{k: v for k, v in analysis.items() if k != 'sha256_hash'}
        )

        serializer = AnalyzedStringSerializer(obj)
        return Response(serializer.data, status=201)

    # --- GET: List strings with optional filters ---
    params = request.query_params
    queryset = AnalyzedString.objects.all()
    filters_applied = {}

    try:
        # --- Boolean filter (is_palindrome) ---
        is_palindrome = params.get('is_palindrome')
        if is_palindrome is not None:
            val = is_palindrome.strip().lower()
            truthy = ['true', '1', 'yes', 'y', 't']
            falsy = ['false', '0', 'no', 'n', 'f']

            if val in truthy:
                filters_applied['is_palindrome'] = True
                queryset = queryset.filter(is_palindrome=True)
            elif val in falsy:
                filters_applied['is_palindrome'] = False
                queryset = queryset.filter(is_palindrome=False)
            else:
                raise ValueError("is_palindrome must be 'true' or 'false'")

        # --- min_length ---
        min_length = params.get('min_length')
        if min_length is not None:
            min_length = int(min_length)
            filters_applied['min_length'] = min_length
            queryset = queryset.filter(length__gte=min_length)

        # --- max_length ---
        max_length = params.get('max_length')
        if max_length is not None:
            max_length = int(max_length)
            filters_applied['max_length'] = max_length
            queryset = queryset.filter(length__lte=max_length)

        # --- word_count ---
        word_count = params.get('word_count')
        if word_count is not None:
            word_count = int(word_count)
            filters_applied['word_count'] = word_count
            queryset = queryset.filter(word_count=word_count)

        # --- contains_character ---
        contains_character = params.get('contains_character')
        if contains_character is not None:
            contains_character = contains_character.strip()
            if len(contains_character) != 1:
                raise ValueError("contains_character must be a single character")
            filters_applied['contains_character'] = contains_character
            queryset = queryset.filter(value__icontains=contains_character)

    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": f"Unexpected error: {str(e)}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    serializer = AnalyzedStringSerializer(queryset, many=True)
    return Response({
        "data": serializer.data,
        "count": queryset.count(),
        "filters_applied": filters_applied
    })


# 🔹 /strings/<value> — GET + DELETE
@api_view(['GET', 'DELETE'])
def string_detail(request, string_value):
    analysis = analyze_string(string_value)
    string_id = analysis["sha256_hash"]

    try:
        obj = AnalyzedString.objects.get(id=string_id)
    except AnalyzedString.DoesNotExist:
        return Response({"error": "String not found"}, status=404)

    # --- GET specific string ---
    if request.method == 'GET':
        serializer = AnalyzedStringSerializer(obj)
        return Response(serializer.data, status=200)

    # --- DELETE string ---
    obj.delete()
    return Response(status=204)


# 🔹 /strings/filter-by-natural-language
@api_view(['GET'])
def natural_language_filter(request):
    query = request.GET.get('query', '').lower()

    filters = {}
    if "palindromic" in query:
        filters["is_palindrome"] = True
    if "single word" in query:
        filters["word_count"] = 1
    if "longer than" in query:
        try:
            num = int(query.split("longer than")[1].split()[0])
            filters["min_length"] = num + 1
        except:
            pass
    if "containing the letter" in query:
        letter = query.split("containing the letter")[-1].strip()
        filters["contains_character"] = letter[0] if letter else None

    if not filters:
        return Response({"error": "Unable to parse query"}, status=400)

    queryset = AnalyzedString.objects.all()
    if filters.get("is_palindrome"):
        queryset = queryset.filter(is_palindrome=True)
    if filters.get("word_count"):
        queryset = queryset.filter(word_count=filters["word_count"])
    if filters.get("min_length"):
        queryset = queryset.filter(length__gte=filters["min_length"])
    if filters.get("contains_character"):
        queryset = queryset.filter(value__icontains=filters["contains_character"])

    serializer = AnalyzedStringSerializer(queryset, many=True)
    return Response({
        "data": serializer.data,
        "count": queryset.count(),
        "interpreted_query": {
            "original": query,
            "parsed_filters": filters
        }
    })