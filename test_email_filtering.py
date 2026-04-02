"""
Test script for email filtering and subject validation.
Tests that only properly formatted codemail requests are processed.
"""

import sys
sys.path.insert(0, '/home/dev/opencodeprojects/codemail')

from email_parser import create_email_parser


def test_valid_codemail_requests():
    """Test that valid codemail requests are parsed correctly."""
    parser = create_email_parser()
    
    print("Testing VALID codemail requests:")
    print("=" * 60)
    
    valid_emails = [
        {
            "subject": "codemail:[my-project] Fix the login bug",
            "body": "Please fix the login button styling.",
            "expected_project": "my-project",
            "expected_instructions": "Fix the login bug"
        },
        {
            "subject": "CODEMAIL:[api-service] Add rate limiting",
            "body": "Implement rate limiting for API endpoints.",
            "expected_project": "api-service",
            "expected_instructions": "Add rate limiting"
        },
        {
            "subject": "Codemail: [frontend-app] Update navigation menu",
            "body": """Update the navigation menu in the header component.
- Add a new 'About' page link
- Make the menu responsive for mobile devices""",
            "expected_project": "frontend-app",
            "expected_instructions": "Update navigation menu"
        },
    ]
    
    all_passed = True
    for i, email_data in enumerate(valid_emails, 1):
        result = parser.parse_email(email_data)
        
        if result is None:
            print(f"❌ Test {i} FAILED: Email was rejected (should have been accepted)")
            print(f"   Subject: {email_data['subject']}")
            all_passed = False
            continue
        
        project_match = result["project_name"] == email_data["expected_project"]
        instructions_match = result["instructions"] == email_data["expected_instructions"]
        
        if project_match and instructions_match:
            print(f"✅ Test {i} PASSED")
            print(f"   Subject: {email_data['subject']}")
            print(f"   Project: {result['project_name']}")
            print(f"   Instructions: {result['instructions'][:50]}...")
        else:
            print(f"❌ Test {i} FAILED")
            print(f"   Subject: {email_data['subject']}")
            if not project_match:
                print(f"   Expected project: {email_data['expected_project']}, got: {result.get('project_name')}")
            if not instructions_match:
                print(f"   Expected instructions: {email_data['expected_instructions']}, got: {result.get('instructions')}")
            all_passed = False
    
    return all_passed


def test_invalid_emails_ignored():
    """Test that invalid emails are properly ignored."""
    parser = create_email_parser()
    
    print("\nTesting INVALID emails (should be ignored):")
    print("=" * 60)
    
    invalid_emails = [
        {
            "subject": "Hello, how are you?",
            "body": "Just checking in!",
            "reason": "No codemail pattern"
        },
        {
            "subject": "[my-project] This should fail",
            "body": "Missing the 'codemail:' prefix",
            "reason": "Missing required prefix"
        },
        {
            "subject": "codemail my-project Fix bug",
            "body": "Missing brackets around project name",
            "reason": "Invalid format - no brackets"
        },
        {
            "subject": "RE: codemail:[project] Previous message",
            "body": "Reply to previous email",
            "reason": "Subject doesn't start with pattern"
        },
        {
            "subject": "",
            "body": "Empty subject",
            "reason": "Empty subject line"
        },
    ]
    
    all_passed = True
    for i, email_data in enumerate(invalid_emails, 1):
        result = parser.parse_email(email_data)
        
        if result is None:
            print(f"✅ Test {i} PASSED - Correctly ignored")
            print(f"   Subject: '{email_data['subject']}'")
            print(f"   Reason: {email_data['reason']}")
        else:
            print(f"❌ Test {i} FAILED - Email should have been ignored")
            print(f"   Subject: '{email_data['subject']}'")
            print(f"   Reason: {email_data['reason']}")
            all_passed = False
    
    return all_passed


def test_email_with_detailed_body():
    """Test that emails with detailed body content work correctly."""
    parser = create_email_parser()
    
    print("\nTesting emails with detailed body content:")
    print("=" * 60)
    
    email_data = {
        "subject": "codemail:[data-pipeline] Optimize ETL process",
        "body": """Please optimize the data pipeline for better performance.

Requirements:
1. Analyze current ETL process bottlenecks
2. Implement batch processing instead of row-by-row
3. Add error handling and retry logic
4. Update documentation with new approach

Files to review:
- src/etl/process.py
- src/etl/transform.py
- docs/pipeline.md"""
    }
    
    result = parser.parse_email(email_data)
    
    if result is None:
        print("❌ FAILED: Email was rejected")
        return False
    
    print("✅ PASSED - Email parsed successfully")
    print(f"   Project: {result['project_name']}")
    print(f"   Instructions: {result['instructions'][:80]}...")
    print(f"   Body length: {len(result['raw_body'])} characters")
    
    return True


def test_case_insensitive_prefix():
    """Test that the prefix is case-insensitive."""
    parser = create_email_parser()
    
    print("\nTesting case-insensitive prefix:")
    print("=" * 60)
    
    prefixes = ["codemail:", "CODEMAIL:", "Codemail:", "CoDeMaIl:"]
    all_passed = True
    
    for prefix in prefixes:
        subject = f"{prefix}[test-project] Test instructions"
        email_data = {"subject": subject, "body": "Test body"}
        
        result = parser.parse_email(email_data)
        
        if result is None:
            print(f"❌ FAILED: '{prefix}' not recognized")
            all_passed = False
        else:
            print(f"✅ PASSED: '{prefix}' correctly recognized")
    
    return all_passed


def test_special_characters_in_project_name():
    """Test project names with special characters."""
    parser = create_email_parser()
    
    print("\nTesting project names with special characters:")
    print("=" * 60)
    
    projects = [
        "my-project",
        "project_123", 
        "api-v2-service",
        "frontend_app",
    ]
    
    all_passed = True
    for project in projects:
        subject = f"codemail:[{project}] Test task"
        email_data = {"subject": subject, "body": "Test"}
        
        result = parser.parse_email(email_data)
        
        if result is None or result["project_name"] != project.lower():
            print(f"❌ FAILED: Project '{project}' not handled correctly")
            all_passed = False
        else:
            print(f"✅ PASSED: Project '{project}' handled correctly")
    
    return all_passed


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("EMAIL FILTERING AND SUBJECT VALIDATION TESTS")
    print("=" * 60 + "\n")
    
    results = []
    
    # Run all test suites
    results.append(("Valid codemail requests", test_valid_codemail_requests()))
    results.append(("Invalid emails ignored", test_invalid_emails_ignored()))
    results.append(("Detailed body content", test_email_with_detailed_body()))
    results.append(("Case insensitive prefix", test_case_insensitive_prefix()))
    results.append(("Special characters in project names", test_special_characters_in_project_name()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} test suites passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Email filtering is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test suite(s) failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
