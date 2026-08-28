# PDF Generation - Frontend Integration Guide

## Overview

The frontend now includes complete PDF generation functionality integrated into the test cases dashboard. Users can download professional PDF reports with a single click.

## Frontend Changes

### 1. API Integration (`src/lib/api.ts`)

**New Function: `downloadTestCasesPDF()`**

```typescript
export const downloadTestCasesPDF = async (
  categoryIds?: number[],
  testTypeIds?: number[],
): Promise<void>
```

**Parameters:**

- `categoryIds` (optional): Array of category IDs to filter
- `testTypeIds` (optional): Array of test type IDs to filter

**Behavior:**

- Constructs URL with proper query parameters
- Fetches PDF from backend endpoint
- Extracts filename from Content-Disposition header
- Triggers browser download
- Throws descriptive errors if generation fails

**Error Handling:**

- Returns 404 if no test cases match filters
- Returns 400 for invalid parameters
- Throws client-friendly error messages

### 2. Dashboard Component (`src/components/test-cases-dashboard.tsx`)

**State Management:**

```typescript
const [isPdfLoading, setIsPdfLoading] = React.useState(false);
const [pdfError, setPdfError] = React.useState<string | null>(null);
```

**Handler Function: `handleDownloadPDF()`**

- Manages loading state during PDF generation
- Passes current filter selections to API
- Catches and displays errors
- Uses useCallback for performance optimization

**UI Components:**

- **PDF Section**: Appears below pagination when test cases exist
- **Error Display**: Shows red error box with detailed messages
- **Test Case Count**: Displays total number of test cases
- **Download Button**:
  - Icon: Download from lucide-react
  - States: Normal, Loading ("Generating PDF..."), Disabled
  - Styling: outline variant for consistency

## User Experience Flow

### Step 1: Filter Test Cases

User selects categories and/or test types from the filter dropdowns.

### Step 2: View Filtered Results

The table displays matching test cases with pagination.

### Step 3: Generate PDF

1. User clicks "Generate PDF Report" button at bottom of table
2. Button shows loading state: "Generating PDF..."
3. Backend generates PDF with filtered data
4. PDF automatically downloads with timestamped filename

### Step 4: Error Handling (if needed)

If PDF generation fails:

1. Error message displays in red box below button
2. User can retry or adjust filters
3. Error auto-clears on next attempt

## Technical Details

### URL Construction

The API is called with query parameters matching the filter state:

```
GET /test-cases/export/pdf?category_ids=1&category_ids=2&test_type_ids=3
```

### Filename Handling

The server provides the filename via Content-Disposition header:

```
Content-Disposition: attachment; filename=test_cases_report_20250827_143022.pdf
```

### Download Mechanism

Uses Blob API for cross-browser compatibility:

1. Fetch PDF as blob
2. Create object URL from blob
3. Create temporary anchor element
4. Trigger click to download
5. Clean up resources

### Loading State

- Button is disabled during PDF generation
- User can see visual feedback ("Generating PDF...")
- Prevents multiple concurrent requests

## Component Props

```typescript
interface TestCasesDashboardProps {
  projectId: number;
}
```

The `projectId` is currently unused (marked with `_projectId`), so PDF generation works for all test cases in the system. This can be enhanced in the future to filter by project.

## Styling and Layout

**PDF Section Container:**

- Border-top for visual separation
- Flexbox layout with gap-3
- Padding for consistency with table

**Error Display:**

- Red background (bg-red-50) with red text (text-red-900)
- Rounded corners for polish
- Bold header with secondary message
- Font-size: xs for details

**Button Styling:**

- outline variant for secondary action
- size-sm for compact footer area
- gap-2 for icon spacing
- Disabled state when loading or no test cases

## Browser Compatibility

- Modern browsers: Blob API supported
- File download: Native browser download
- No dependencies beyond existing libraries
- Works in Chrome, Firefox, Safari, Edge

## Performance Considerations

- PDF generation happens on backend (not frontend)
- Blob download is efficient and non-blocking
- Button disable state prevents duplicate requests
- Loading indicator gives user feedback

## Integration Checklist

- [x] API function created (`downloadTestCasesPDF`)
- [x] Download icon imported
- [x] State management added (loading, error)
- [x] Handler function implemented
- [x] UI button added below pagination
- [x] Error display implemented
- [x] Loading state handled
- [x] Styling consistent with design
- [x] TypeScript types properly defined
- [x] ESLint validation passed

## Testing Recommendations

### Unit Tests

```typescript
// Test the downloadTestCasesPDF function
// Mock fetch for success and error cases
// Verify URL construction with filters
// Test blob creation and download
```

### Integration Tests

```typescript
// Test button click triggers download
// Test loading state during generation
// Test error display on failure
// Test filter state is passed correctly
```

### Manual Testing

1. Open test cases dashboard
2. Apply filters (categories, test types)
3. Click "Generate PDF Report" button
4. Verify PDF downloads with correct data
5. Verify filename includes timestamp
6. Test with no filters
7. Test error handling by providing invalid filters

## Future Enhancements

### Phase 1 (Current)

✓ Basic PDF download with filters
✓ Error handling and loading states
✓ Integration with existing filters

### Phase 2 (Future)

- [ ] Custom report templates
- [ ] Additional export formats (Excel, HTML)
- [ ] Report scheduling and email delivery
- [ ] Custom company branding in PDFs
- [ ] Advanced filtering options
- [ ] Report history and archival

### Phase 3 (Future)

- [ ] Real-time report preview
- [ ] Batch report generation
- [ ] Report comparison tools
- [ ] Trend analysis and statistics
- [ ] Audit trail logging

## Troubleshooting

### PDF Download Not Triggering

- Check browser console for errors
- Verify backend URL in config
- Ensure backend service is running
- Check CORS settings if applicable

### Error Messages Appear

- Review error message for details
- Verify filters are valid
- Check that test cases match filters
- Review backend logs for server-side issues

### Filename Not Preserved

- Some browsers may rename files
- Check browser download settings
- Verify Content-Disposition header is sent
- Try different browser if issue persists

## API Reference

### Endpoint

**GET** `/test-cases/export/pdf`

### Query Parameters

| Parameter     | Type  | Description                          |
| ------------- | ----- | ------------------------------------ |
| category_ids  | array | Category IDs to filter (repeatable)  |
| test_type_ids | array | Test type IDs to filter (repeatable) |

### Response

- **200 OK**: PDF file (application/pdf)
- **404 Not Found**: No test cases match filters
- **400 Bad Request**: Invalid parameters

### Example cURL

```bash
curl -X GET "http://localhost:8000/test-cases/export/pdf?category_ids=1&test_type_ids=2" \
  -H "Accept: application/pdf" \
  -o report.pdf
```

## Files Modified Summary

### Frontend

- `src/lib/api.ts` - Added PDF download function
- `src/components/test-cases-dashboard.tsx` - Added UI and integration

### Backend (Already Implemented)

- `app/pdf_generator.py` - PDF generation module
- `app/routers/test_cases.py` - Export endpoint
- `requirements.txt` - Dependencies added

## Deployment Checklist

- [x] Backend PDF generation working
- [x] Frontend integration complete
- [x] Testing passed (linting)
- [x] Documentation complete
- [ ] Deploy backend changes
- [ ] Deploy frontend changes
- [ ] Verify in production
- [ ] Monitor for issues

## Support and Maintenance

For issues or questions about PDF generation functionality:

1. Check the troubleshooting section
2. Review backend logs
3. Verify API endpoint accessibility
4. Check browser console for errors
5. Consult the comprehensive documentation
