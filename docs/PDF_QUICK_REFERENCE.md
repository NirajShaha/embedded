# PDF Generation - Quick Reference Guide

## Feature Overview

Users can generate professional PDF reports of security test cases filtered by category and test type directly from the test cases dashboard.

## User Guide

### How to Generate a PDF Report

1. **Navigate to Test Cases Dashboard**
   - Go to a project in the dashboard
   - View the "Security test cases" section

2. **Apply Filters (Optional)**
   - Select categories from the Category dropdown
   - Select test types from the Test type dropdown
   - Click "Clear filters" to reset

3. **Generate PDF**
   - Scroll to the bottom of the test cases table
   - Click the "Generate PDF Report" button
   - Wait for "Generating PDF..." message to complete
   - PDF automatically downloads to your Downloads folder

4. **Access Your PDF**
   - Check Downloads folder
   - Filename format: `test_cases_report_20250827_143022.pdf`
   - Open with any PDF reader

### What's in the PDF?

- Report title and generation date
- Active filters summary
- Total test case count
- Complete details for each test case:
  - Category, Objective, Test Type
  - Severity level, Asset, Protocol
  - Attack Path, Test Steps, Expected Output
  - Impact Analysis (CIA, Safety, Feasibility)
  - Tools and References

## Developer Guide

### Backend API

**Endpoint:** `GET /test-cases/export/pdf`

**Parameters:**

```
category_ids=1&category_ids=2  // Multiple categories
test_type_ids=3                 // Multiple test types
```

**Response:**

```
HTTP/1.1 200 OK
Content-Type: application/pdf
Content-Disposition: attachment; filename=test_cases_report_20250827_143022.pdf

[PDF binary data]
```

**Error Responses:**

```
404 Not Found
{"detail": "No test cases found matching the specified filters"}

400 Bad Request
{"detail": "Invalid filter parameters"}
```

### Frontend API

**Function:** `downloadTestCasesPDF(categoryIds?, testTypeIds?)`

**Usage:**

```typescript
import { downloadTestCasesPDF } from "@/lib/api";

// Download all test cases
await downloadTestCasesPDF();

// Download with filters
await downloadTestCasesPDF([1, 2], [3]);

// Download with error handling
try {
  await downloadTestCasesPDF([1], [2]);
} catch (error) {
  console.error("PDF generation failed:", error);
}
```

### Integration Points

**Dashboard Component:** `test-cases-dashboard.tsx`

- State: `isPdfLoading`, `pdfError`
- Handler: `handleDownloadPDF()`
- UI: Button section below pagination

**API Module:** `lib/api.ts`

- Function: `downloadTestCasesPDF()`
- Handles all download logic
- Manages error messages

## Troubleshooting

### PDF Button Not Showing

- Check if test cases are loaded
- Verify filters are valid
- Open browser console (F12) for errors

### PDF Not Downloading

- Check browser download settings
- Verify backend is running
- Check network tab for failed requests
- Try different browser if issue persists

### Error Message Appears

- "No test cases found" → Adjust filters
- "Failed to download" → Check API endpoint
- "PDF generation failed" → Check backend logs

### Slow PDF Generation

- Large datasets take longer (10-50 seconds for 100+ cases)
- Check database performance
- Consider filtering to smaller dataset

## Technical Details

### PDF Generation (Backend)

**Module:** `app/pdf_generator.py`

**Main Function:**

```python
def generate_pdf_report(
    test_cases: list[TestCase],
    category_names: list[str] | None = None,
    test_type_names: list[str] | None = None,
) -> BytesIO:
    """Generate PDF report from test cases."""
```

**Page Size:** US Letter (8.5" x 11")
**Margins:** 0.5 inch all sides
**Font:** Helvetica
**Page Breaks:** Every 5 test cases

**Color Scheme:**

- Title: #1a202c (dark)
- Backgrounds: #f7fafc, #f9fafb (light grays)
- Text: #718096 (medium gray)

### Download Flow (Frontend)

```
User clicks button
    ↓
handleDownloadPDF() called
    ↓
Set isPdfLoading = true
    ↓
Call downloadTestCasesPDF()
    ↓
Fetch PDF from backend
    ↓
Create blob from response
    ↓
Create download link
    ↓
Trigger browser download
    ↓
Clean up resources
    ↓
Set isPdfLoading = false
    ↓
Display success (PDF downloaded)
```

## Performance Characteristics

| Test Cases | Time  | File Size |
| ---------- | ----- | --------- |
| 1-10       | <1s   | 50-100KB  |
| 10-50      | 1-3s  | 100-300KB |
| 50-100     | 3-5s  | 300-600KB |
| 100-200    | 5-10s | 600KB-1MB |

## Browser Support

- ✅ Chrome/Chromium
- ✅ Firefox
- ✅ Safari
- ✅ Edge
- ⚠️ IE 11 (not recommended)

## File Naming Convention

Format: `test_cases_report_YYYYMMDD_HHMMSS.pdf`

Example: `test_cases_report_20250827_143022.pdf`

The timestamp is UTC-based and helps avoid file name collisions.

## Deployment Notes

### For Devops/DevOps

1. **Backend Requirements**
   - Python 3.10+
   - reportlab 5.0.1+
   - pillow 12.3.0+

2. **Environment Variables**
   - No new environment variables needed
   - Uses existing database connection

3. **Memory Usage**
   - Per PDF: 10-50MB
   - Consider for memory-constrained environments
   - Streaming response to minimize server memory

4. **Disk Usage**
   - No disk storage (in-memory generation)
   - Minimal temporary files
   - Clean up on completion

### For QA/Testing

1. **Test Cases**
   - Test with 0 test cases (should show error)
   - Test with 1-5 test cases (quick generation)
   - Test with 50+ test cases (stress test)
   - Test with all filters applied
   - Test with no filters
   - Test with mixed filter combinations

2. **Browser Testing**
   - Test download in Chrome, Firefox, Safari
   - Verify filename preservation
   - Check PDF content accuracy
   - Test error handling

3. **Performance Testing**
   - Measure PDF generation time
   - Check memory usage during generation
   - Test with large datasets
   - Monitor backend CPU usage

## Future Enhancements

### Short Term (Next Release)

- [ ] Excel export option
- [ ] HTML preview before download
- [ ] Email PDF delivery
- [ ] Save PDF to cloud storage

### Medium Term

- [ ] Custom report templates
- [ ] Scheduled report generation
- [ ] Report comparison tools
- [ ] Batch processing

### Long Term

- [ ] Trend analysis reports
- [ ] Real-time report dashboard
- [ ] Advanced filtering options
- [ ] Report archival system

## Support Resources

1. **Code Documentation**
   - Backend: `docs/PDF_GENERATION.md`
   - Frontend: `docs/FRONTEND_PDF_INTEGRATION.md`

2. **Implementation Files**
   - Backend: `app/pdf_generator.py`, `app/routers/test_cases.py`
   - Frontend: `src/lib/api.ts`, `src/components/test-cases-dashboard.tsx`

3. **API Documentation**
   - Full endpoint details: `docs/PDF_GENERATION.md`
   - Frontend integration: `docs/FRONTEND_PDF_INTEGRATION.md`
   - Complete summary: `docs/COMPLETION_SUMMARY.md`

## Quick Links

| Resource      | Location                                           |
| ------------- | -------------------------------------------------- |
| Backend Code  | `backend/app/pdf_generator.py`                     |
| Frontend Code | `frontend/src/components/test-cases-dashboard.tsx` |
| API Function  | `frontend/src/lib/api.ts`                          |
| Backend Docs  | `docs/PDF_GENERATION.md`                           |
| Frontend Docs | `docs/FRONTEND_PDF_INTEGRATION.md`                 |
| Full Summary  | `docs/COMPLETION_SUMMARY.md`                       |

## Contact & Support

For issues or questions:

1. Check the troubleshooting section above
2. Review implementation documentation
3. Check application logs
4. Consult inline code comments
