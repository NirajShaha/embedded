# PDF Generation for Test Cases - Implementation Guide

## Overview

This implementation adds PDF report generation functionality for security test cases. Users can generate professional, enterprise-standard PDF reports filtered by category and test type.

## Backend Implementation

### Files Added/Modified

#### 1. `backend/requirements.txt`

Added dependencies:

- `reportlab` (v5.0.1) - Professional PDF generation library
- `pillow` (v12.3.0) - Image handling for reportlab

#### 2. `backend/app/pdf_generator.py` (NEW)

Core PDF generation module with the following functions:

**`generate_pdf_report(test_cases, category_names, test_type_names) -> BytesIO`**

- Main function to generate PDF reports
- Parameters:
  - `test_cases`: List of TestCase ORM objects
  - `category_names`: Optional list of category names for display
  - `test_type_names`: Optional list of test type names for display
- Returns: BytesIO object containing PDF data
- Features:
  - Professional enterprise formatting
  - A4/Letter page size with margins
  - Color-coded sections
  - Page breaks for readability (every 5 test cases)
  - Timestamp-based file naming

**Helper Functions:**

- `_format_text(text, max_length)`: Sanitizes and truncates text for PDF
- `_build_header()`: Creates document header with title and metadata
- `_build_test_case_section()`: Formats individual test case with all details

#### 3. `backend/app/routers/test_cases.py` (MODIFIED)

Added new endpoint:

**`GET /test-cases/export/pdf`**

- Purpose: Generate and download PDF report of filtered test cases
- Query Parameters:
  - `category_ids` (optional): Multiple category IDs (e.g., `?category_ids=1&category_ids=2`)
  - `test_type_ids` (optional): Multiple test type IDs
  - `category_id` (deprecated): Single category ID (for backward compatibility)
  - `test_type_id` (deprecated): Single test type ID (for backward compatibility)
- Response:
  - Media Type: `application/pdf`
  - Filename: `test_cases_report_YYYYMMDD_HHMMSS.pdf` (e.g., `test_cases_report_20250827_143022.pdf`)
  - Content: PDF file for download
- Error Handling:
  - Returns 404 if no test cases match the filters
  - Proper error messages in response
- Special Handling:
  - Respects the "Both" wildcard filter for test types
  - Uses same filtering logic as `list_test_cases` endpoint

### PDF Report Structure

The generated PDF includes:

1. **Header Section**
   - Report title: "Security Test Cases Report"
   - Generation date and time
   - Applied filters (Categories and Test Types)

2. **Summary**
   - Total number of test cases in report

3. **Test Case Details** (for each test case)
   - Test Case Number and Title
   - Key Details Table:
     - Category, Objective, Test Type
     - Severity (with rank), Asset
     - Protocol, Attack Vector
     - Source/Scope Status, Automation Possible
   - Full Description Fields:
     - Action/Test Case description
     - Description
     - Attack Path
     - Test Steps
     - Expected Output
     - Attack Feasibility
     - CIA Impact
     - Safety Impact
     - Threat information
     - Tools used
     - References

4. **Formatting**
   - Professional font styling (Helvetica)
   - Color-coded severity levels (if available)
   - Alternating row colors in tables for readability
   - Proper spacing and margins
   - Page breaks every 5 test cases to prevent overcrowding

## API Usage Examples

### cURL

```bash
# Export all test cases
curl -X GET "http://localhost:8000/test-cases/export/pdf" \
  -H "Accept: application/pdf" \
  -o report.pdf

# Export filtered by category (IDs: 1, 2)
curl -X GET "http://localhost:8000/test-cases/export/pdf?category_ids=1&category_ids=2" \
  -H "Accept: application/pdf" \
  -o report_filtered.pdf

# Export filtered by test type (IDs: 3, 4) and category (ID: 1)
curl -X GET "http://localhost:8000/test-cases/export/pdf?category_ids=1&test_type_ids=3&test_type_ids=4" \
  -H "Accept: application/pdf" \
  -o report_combined.pdf
```

### Python (with requests)

```python
import requests

response = requests.get(
    "http://localhost:8000/test-cases/export/pdf",
    params={"category_ids": [1, 2]},
    headers={"Accept": "application/pdf"}
)

if response.status_code == 200:
    with open("report.pdf", "wb") as f:
        f.write(response.content)
else:
    print(f"Error: {response.status_code} - {response.text}")
```

### JavaScript/TypeScript (Frontend)

```typescript
// Function to call the PDF generation endpoint
async function downloadTestCasesPDF(
  categoryIds?: number[],
  testTypeIds?: number[],
) {
  const params = new URLSearchParams();

  if (categoryIds?.length) {
    categoryIds.forEach((id) => params.append("category_ids", id.toString()));
  }

  if (testTypeIds?.length) {
    testTypeIds.forEach((id) => params.append("test_type_ids", id.toString()));
  }

  const response = await fetch(`/api/test-cases/export/pdf?${params}`, {
    method: "GET",
  });

  if (response.ok) {
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "test_cases_report.pdf";
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  } else {
    console.error("Failed to generate PDF");
  }
}
```

## Frontend Integration (Optional - Not Implemented)

To add a "Generate PDF" button to the frontend dashboard, the following changes would be needed:

1. **Create API function in `src/lib/api.ts`:**

```typescript
export async function downloadTestCasePDF(
  categoryIds?: number[],
  testTypeIds?: number[],
): Promise<void> {
  const params = new URLSearchParams();

  if (categoryIds?.length) {
    categoryIds.forEach((id) => params.append("category_ids", id.toString()));
  }

  if (testTypeIds?.length) {
    testTypeIds.forEach((id) => params.append("test_type_ids", id.toString()));
  }

  const response = await fetch(
    `${API_BASE_URL}/test-cases/export/pdf?${params}`,
  );

  if (!response.ok) {
    throw new Error("Failed to generate PDF");
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `test_cases_report_${new Date().toISOString().slice(0, 10)}.pdf`;
  a.click();
  window.URL.revokeObjectURL(url);
}
```

2. **Add button to `src/components/test-cases-dashboard.tsx`:**

```typescript
<Button
  variant="outline"
  size="sm"
  onClick={() => downloadTestCasePDF(selectedCategories, selectedTestTypes)}
  disabled={!hasFilters}
  className="self-end"
>
  <Download className="mr-2 size-4" />
  Generate PDF
</Button>
```

## Error Handling

The API returns appropriate HTTP status codes and error messages:

- **200 OK**: PDF generated successfully
- **404 Not Found**: No test cases match the specified filters
  - Response body: `{"detail": "No test cases found matching the specified filters"}`
- **400 Bad Request**: Invalid query parameters

## Performance Considerations

- PDF generation is done synchronously on request (suitable for small to medium datasets)
- For large datasets (>100 test cases), consider:
  - Adding async/background job processing using Celery or similar
  - Implementing caching for frequently requested reports
  - Streaming PDF generation directly to response

## Testing the Implementation

1. **Start the backend server:**

   ```bash
   cd backend
   python run.py
   ```

2. **Test with cURL:**

   ```bash
   curl -X GET "http://localhost:8000/test-cases/export/pdf" \
     -H "Accept: application/pdf" \
     -o test_report.pdf && echo "PDF generated successfully"
   ```

3. **Verify the PDF:**
   - Open the generated PDF file in any PDF reader
   - Verify headers, test case details, and formatting

## Future Enhancements

1. Add filtering options:
   - By severity level
   - By date range
   - By automation possibility
   - By specific test type

2. Styling improvements:
   - Add company logo/branding
   - Custom color schemes
   - QR codes for test tracking

3. Additional formats:
   - Excel export (.xlsx)
   - HTML report
   - Markdown report

4. Advanced features:
   - Test case comparison reports
   - Trend analysis over time
   - Custom report templates
   - Email delivery of reports
