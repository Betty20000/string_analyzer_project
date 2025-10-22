from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import AnalyzedString
from .serializers import AnalyzedStringSerializer
from .utils import analyze_string

# 1️⃣ Create/Analyze String
@api_view(['POST'])
def create_string(request):
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


# 2️⃣ Get Specific String
@api_view(['GET'])
def get_string(request, string_value):
    analysis = analyze_string(string_value)
    try:
        obj = AnalyzedString.objects.get(id=analysis["sha256_hash"])
        serializer = AnalyzedStringSerializer(obj)
        return Response(serializer.data)
    except AnalyzedString.DoesNotExist:
        return Response({"error": "String not found"}, status=404)


# 3️⃣ Get All Strings (Filtering)
@api_view(['GET'])
def list_strings(request):
    queryset = AnalyzedString.objects.all()

    # Apply filters
    if 'is_palindrome' in request.GET:
        queryset = queryset.filter(is_palindrome=request.GET['is_palindrome'].lower() == 'true')
    if 'min_length' in request.GET:
        queryset = queryset.filter(length__gte=int(request.GET['min_length']))
    if 'max_length' in request.GET:
        queryset = queryset.filter(length__lte=int(request.GET['max_length']))
    if 'word_count' in request.GET:
        queryset = queryset.filter(word_count=int(request.GET['word_count']))
    if 'contains_character' in request.GET:
        queryset = queryset.filter(value__icontains=request.GET['contains_character'])

    serializer = AnalyzedStringSerializer(queryset, many=True)
    return Response({
        "data": serializer.data,
        "count": queryset.count(),
        "filters_applied": request.GET.dict()
    })


# 5️⃣ Delete String
@api_view(['DELETE'])
def delete_string(request, string_value):
    analysis = analyze_string(string_value)
    try:
        obj = AnalyzedString.objects.get(id=analysis["sha256_hash"])
        obj.delete()
        return Response(status=204)
    except AnalyzedString.DoesNotExist:
        return Response({"error": "String not found"}, status=404)

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

    # Apply filters
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