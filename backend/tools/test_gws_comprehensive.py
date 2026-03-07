#!/usr/bin/env python3
"""
JAWIR OS - Comprehensive Google Workspace Test
Tests all Google Workspace features: Gmail, Drive, Calendar, Sheets, Forms, Docs
"""

import sys
sys.path.insert(0, '.')

from google_workspace import GoogleWorkspaceMCP

def main():
    print('='*70)
    print('JAWIR OS - COMPREHENSIVE GOOGLE WORKSPACE TEST')
    print('='*70)

    mcp = GoogleWorkspaceMCP()
    print(f'Connected as: {mcp.user_email}')
    print(f'Tools enabled: {mcp.tools_enabled}')

    results = []

    # TEST 1: GMAIL
    print('\n' + '='*70)
    print('TEST 1: GMAIL')
    print('='*70)

    # 1.1 List labels
    print('\n1.1 Gmail Labels...')
    try:
        result = mcp.list_gmail_labels()
        status = 'PASS' if result['success'] else 'FAIL'
        if not result['success']:
            print(f'   Error: {result.get("error", "Unknown")}')
    except Exception as e:
        status = 'FAIL'
        print(f'   Exception: {e}')
    print(f'   {status}')
    results.append(('Gmail Labels', status))

    # 1.2 Search Gmail
    print('\n1.2 Gmail Search...')
    try:
        result = mcp.search_gmail('from:google', 3)
        status = 'PASS' if result['success'] else 'FAIL'
        if not result['success']:
            print(f'   Error: {result.get("error", "Unknown")}')
    except Exception as e:
        status = 'FAIL'
        print(f'   Exception: {e}')
    print(f'   {status}')
    results.append(('Gmail Search', status))

    # 1.3 Send Email
    print('\n1.3 Gmail Send...')
    try:
        result = mcp.send_email('hazzikiraju@gmail.com', 'JAWIR OS Comprehensive Test', 'Test email dari comprehensive testing JAWIR OS.')
        status = 'PASS' if result['success'] else 'FAIL'
        if result['success']:
            print(f'   Output: {result["output"]}')
        else:
            print(f'   Error: {result.get("error", "Unknown")}')
    except Exception as e:
        status = 'FAIL'
        print(f'   Exception: {e}')
    print(f'   {status}')
    results.append(('Gmail Send', status))

    # TEST 2: DRIVE
    print('\n' + '='*70)
    print('TEST 2: DRIVE')
    print('='*70)

    # 2.1 List/Search files
    print('\n2.1 Drive Search...')
    try:
        result = mcp.search_drive_files('*')
        status = 'PASS' if result['success'] else 'FAIL'
        if result['success']:
            print(f'   Found files in drive')
        else:
            print(f'   Error: {result.get("error", "Unknown")}')
    except Exception as e:
        status = 'FAIL'
        print(f'   Exception: {e}')
    print(f'   {status}')
    results.append(('Drive Search', status))

    # 2.2 Create folder
    print('\n2.2 Drive Create Folder...')
    try:
        result = mcp.create_drive_folder('JAWIR_Test_Folder')
        status = 'PASS' if result['success'] else 'FAIL'
        if result['success']:
            print(f'   Output: {result["output"][:100]}...')
        else:
            print(f'   Error: {result.get("error", "Unknown")}')
    except Exception as e:
        status = 'FAIL'
        print(f'   Exception: {e}')
    print(f'   {status}')
    results.append(('Drive Create Folder', status))

    # TEST 3: CALENDAR
    print('\n' + '='*70)
    print('TEST 3: CALENDAR')
    print('='*70)

    # 3.1 List calendars
    print('\n3.1 Calendar List...')
    try:
        result = mcp.list_calendars()
        status = 'PASS' if result['success'] else 'FAIL'
        if not result['success']:
            print(f'   Error: {result.get("error", "Unknown")}')
    except Exception as e:
        status = 'FAIL'
        print(f'   Exception: {e}')
    print(f'   {status}')
    results.append(('Calendar List', status))

    # 3.2 List events
    print('\n3.2 Calendar Events...')
    try:
        result = mcp.list_calendar_events()
        status = 'PASS' if result['success'] else 'FAIL'
        if not result['success']:
            print(f'   Error: {result.get("error", "Unknown")}')
    except Exception as e:
        status = 'FAIL'
        print(f'   Exception: {e}')
    print(f'   {status}')
    results.append(('Calendar Events', status))

    # 3.3 Create event
    print('\n3.3 Calendar Create Event...')
    try:
        # Use ISO format with timezone offset
        result = mcp.add_calendar_event(
            summary='JAWIR OS Test Event',
            start_time='2025-02-01T10:00:00+07:00',
            end_time='2025-02-01T11:00:00+07:00',
            description='Event test dari comprehensive testing'
        )
        status = 'PASS' if result['success'] else 'FAIL'
        if result['success']:
            print(f'   Output: {result["output"][:100]}...')
        else:
            print(f'   Error: {result.get("error", "Unknown")}')
    except Exception as e:
        status = 'FAIL'
        print(f'   Exception: {e}')
    print(f'   {status}')
    results.append(('Calendar Create Event', status))

    # TEST 4: SHEETS
    print('\n' + '='*70)
    print('TEST 4: SHEETS')
    print('='*70)

    # 4.1 Create spreadsheet
    print('\n4.1 Sheets Create...')
    try:
        result = mcp.create_spreadsheet('JAWIR Test Spreadsheet')
        status = 'PASS' if result['success'] else 'FAIL'
        if result['success']:
            print(f'   Output: {result["output"][:100]}...')
        else:
            print(f'   Error: {result.get("error", "Unknown")}')
    except Exception as e:
        status = 'FAIL'
        print(f'   Exception: {e}')
    print(f'   {status}')
    results.append(('Sheets Create', status))

    # TEST 5: FORMS
    print('\n' + '='*70)
    print('TEST 5: FORMS')
    print('='*70)

    # 5.1 Create form
    print('\n5.1 Forms Create...')
    try:
        result = mcp.create_form('JAWIR Test Form', 'Form test dari comprehensive testing')
        status = 'PASS' if result['success'] else 'FAIL'
        if result['success']:
            print(f'   Output: {result["output"][:150]}...')
        else:
            print(f'   Error: {result.get("error", "Unknown")}')
    except Exception as e:
        status = 'FAIL'
        print(f'   Exception: {e}')
    print(f'   {status}')
    results.append(('Forms Create', status))

    # TEST 6: DOCS
    print('\n' + '='*70)
    print('TEST 6: DOCS')
    print('='*70)

    # 6.1 Create doc
    print('\n6.1 Docs Create...')
    doc_id = None
    try:
        result = mcp.create_doc('JAWIR Test Document', 'Dokumen test dari JAWIR OS comprehensive testing.')
        status = 'PASS' if result['success'] else 'FAIL'
        if result['success']:
            print(f'   Output: {result["output"]}')
            # Try to extract doc ID for further tests
            # Format: "Created Google Doc 'xxx' (ID: 1abc123) for user@email.com. Link: ..."
            output = result["output"]
            import re
            id_match = re.search(r'\(ID:\s*([a-zA-Z0-9_-]+)\)', output)
            if id_match:
                doc_id = id_match.group(1)
                print(f'   Extracted Doc ID: {doc_id}')
        else:
            print(f'   Error: {result.get("error", "Unknown")}')
    except Exception as e:
        status = 'FAIL'
        print(f'   Exception: {e}')
    print(f'   {status}')
    results.append(('Docs Create', status))

    # 6.2 Search docs
    print('\n6.2 Docs Search...')
    try:
        result = mcp.search_docs('JAWIR')
        status = 'PASS' if result['success'] else 'FAIL'
        if result['success']:
            print(f'   Output: {result["output"][:100]}...')
        else:
            print(f'   Error: {result.get("error", "Unknown")}')
    except Exception as e:
        status = 'FAIL'
        print(f'   Exception: {e}')
    print(f'   {status}')
    results.append(('Docs Search', status))

    # 6.3 List docs in folder
    print('\n6.3 Docs List...')
    try:
        result = mcp.list_docs_in_folder('root', 5)
        status = 'PASS' if result['success'] else 'FAIL'
        if result['success']:
            print(f'   Output: {result["output"][:100]}...')
        else:
            print(f'   Error: {result.get("error", "Unknown")}')
    except Exception as e:
        status = 'FAIL'
        print(f'   Exception: {e}')
    print(f'   {status}')
    results.append(('Docs List', status))

    # 6.4 Get doc content (if we have doc_id)
    print('\n6.4 Docs Get Content...')
    if doc_id:
        try:
            result = mcp.get_doc_content(doc_id)
            status = 'PASS' if result['success'] else 'FAIL'
            if result['success']:
                print(f'   Retrieved document content')
            else:
                print(f'   Error: {result.get("error", "Unknown")}')
        except Exception as e:
            status = 'FAIL'
            print(f'   Exception: {e}')
    else:
        status = 'SKIP'
        print('   Skipped - no doc_id available')
    print(f'   {status}')
    results.append(('Docs Get Content', status))

    # SUMMARY
    print('\n' + '='*70)
    print('SUMMARY')
    print('='*70)
    passed = sum(1 for _, s in results if s == 'PASS')
    skipped = sum(1 for _, s in results if s == 'SKIP')
    failed = sum(1 for _, s in results if s == 'FAIL')
    total = len(results)
    
    print(f'\nTotal: {passed} PASS, {failed} FAIL, {skipped} SKIP (out of {total} tests)')
    print()
    for name, status in results:
        if status == 'PASS':
            icon = '✓'
        elif status == 'FAIL':
            icon = '✗'
        else:
            icon = '-'
        print(f'  [{icon}] {name}: {status}')
    print()
    print('='*70)
    
    if failed == 0:
        print('ALL TESTS PASSED! Google Workspace integration working correctly.')
    else:
        print(f'WARNING: {failed} test(s) failed!')
    print('='*70)

if __name__ == '__main__':
    main()
