#!/usr/bin/env python3
"""
Comprehensive Web Application Tester
====================================

Automatically tests all navigation links, validates pages, and identifies issues.
Uses OpenAI to analyze and report on web application health.
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import os
import openai
from dotenv import load_dotenv

load_dotenv()

class WebAppTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "base_url": base_url,
            "pages_tested": [],
            "errors": [],
            "warnings": [],
            "summary": {}
        }
        
        # Initialize OpenAI
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
            print("🤖 OpenAI API available for analysis")
        else:
            print("⚠️ No OpenAI API key found - analysis will be limited")
    
    def test_all_pages(self):
        """Test all navigation pages defined in the sidebar."""
        # Pages from the sidebar navigation
        pages_to_test = [
            ("/", "Home (Today's CC)"),
            ("/todays-cc", "Today's CC"),
            ("/knowledge-hub", "Knowledge Hub"),
            ("/agent-command-center", "Agent Command Center"),
            ("/prompt-library", "Prompt Library"),
            ("/github-users", "GitHub Users"),
            ("/youtube-channels", "YouTube Channels"),
            ("/tasks", "Tasks"),
            ("/habits", "Habits"),
            ("/shopping-list", "Shopping List"),
            ("/notes", "Notes"),
            ("/books", "Books"),
            ("/journals", "Journals"),
            ("/maintenance-schedule", "Maintenance"),
            ("/model-testing", "Model Testing"),
            ("/voice-commands", "Voice Commands"),
            ("/workflow-templates", "Workflows"),
            ("/agent-results", "Agent Results"),
            ("/cost-tracking", "Cost Tracking"),
        ]
        
        print(f"🧪 Testing {len(pages_to_test)} pages...")
        
        for url_path, page_name in pages_to_test:
            result = self.test_page(url_path, page_name)
            self.results["pages_tested"].append(result)
            time.sleep(0.1)  # Small delay to avoid overwhelming the server
        
        return self.analyze_results()
    
    def test_page(self, url_path: str, page_name: str) -> Dict[str, Any]:
        """Test a single page and return detailed results."""
        full_url = f"{self.base_url}{url_path}"
        
        print(f"  📄 Testing {page_name}: {url_path}")
        
        try:
            response = self.session.get(full_url, timeout=10)
            
            result = {
                "url_path": url_path,
                "page_name": page_name,
                "full_url": full_url,
                "status_code": response.status_code,
                "response_time_ms": response.elapsed.total_seconds() * 1000,
                "content_length": len(response.content),
                "content_type": response.headers.get('content-type', ''),
                "success": False,
                "errors": [],
                "warnings": []
            }
            
            # Check status code
            if response.status_code == 200:
                result["success"] = True
                print(f"    ✅ {page_name} - OK ({response.status_code})")
            elif response.status_code == 302:
                result["success"] = True
                result["warnings"].append("Redirected (302)")
                print(f"    🔄 {page_name} - Redirected ({response.status_code})")
            else:
                result["errors"].append(f"HTTP {response.status_code}")
                print(f"    ❌ {page_name} - Error {response.status_code}")
            
            # Check content
            if response.status_code in [200, 302]:
                content = response.text.lower()
                
                # Check for common error patterns
                error_patterns = [
                    ("templatenotfound", "Template file missing"),
                    ("jinja2.exceptions", "Template rendering error"),
                    ("500 internal server error", "Server error"),
                    ("undefined", "Undefined variable in template"),
                    ("syntax error", "Syntax error"),
                ]
                
                for pattern, description in error_patterns:
                    if pattern in content:
                        result["errors"].append(description)
                        print(f"    ⚠️  Found: {description}")
                
                # Check for good indicators
                if "lifeos" in content and "notion" in content:
                    result["has_branding"] = True
                
                if len(content) < 1000:
                    result["warnings"].append("Content seems short")
            
            return result
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Connection error: {str(e)}"
            print(f"    ❌ {page_name} - {error_msg}")
            
            return {
                "url_path": url_path,
                "page_name": page_name,
                "full_url": full_url,
                "success": False,
                "errors": [error_msg],
                "warnings": []
            }
    
    def analyze_results(self) -> Dict[str, Any]:
        """Analyze test results and generate summary."""
        total_pages = len(self.results["pages_tested"])
        successful_pages = len([p for p in self.results["pages_tested"] if p["success"]])
        failed_pages = total_pages - successful_pages
        
        # Collect all errors
        all_errors = []
        all_warnings = []
        
        for page in self.results["pages_tested"]:
            all_errors.extend(page.get("errors", []))
            all_warnings.extend(page.get("warnings", []))
        
        self.results["summary"] = {
            "total_pages": total_pages,
            "successful_pages": successful_pages,
            "failed_pages": failed_pages,
            "success_rate": (successful_pages / total_pages * 100) if total_pages > 0 else 0,
            "total_errors": len(all_errors),
            "total_warnings": len(all_warnings),
            "unique_errors": list(set(all_errors)),
            "unique_warnings": list(set(all_warnings))
        }
        
        # Print summary
        print(f"\n📊 Test Results Summary:")
        print(f"  📄 Pages tested: {total_pages}")
        print(f"  ✅ Successful: {successful_pages}")
        print(f"  ❌ Failed: {failed_pages}")
        print(f"  📈 Success rate: {self.results['summary']['success_rate']:.1f}%")
        print(f"  🐛 Total errors: {len(all_errors)}")
        print(f"  ⚠️  Total warnings: {len(all_warnings)}")
        
        if self.results['summary']['unique_errors']:
            print(f"\n🔍 Unique errors found:")
            for error in self.results['summary']['unique_errors']:
                print(f"    • {error}")
        
        if self.results['summary']['unique_warnings']:
            print(f"\n⚠️  Warnings:")
            for warning in self.results['summary']['unique_warnings']:
                print(f"    • {warning}")
        
        return self.results
    
    def get_ai_analysis(self) -> str:
        """Use OpenAI to analyze test results and provide recommendations."""
        if not self.openai_api_key:
            return "AI analysis not available (no OpenAI API key)"
        
        try:
            prompt = f"""
            Analyze this web application test report and provide actionable recommendations:

            Test Summary:
            - Total pages: {self.results['summary']['total_pages']}
            - Success rate: {self.results['summary']['success_rate']:.1f}%
            - Failed pages: {self.results['summary']['failed_pages']}
            - Unique errors: {self.results['summary']['unique_errors']}
            - Unique warnings: {self.results['summary']['unique_warnings']}

            Failed pages details:
            {json.dumps([p for p in self.results['pages_tested'] if not p['success']], indent=2)}

            Please provide:
            1. Overall assessment of the web application health
            2. Priority issues that need immediate attention
            3. Specific recommendations for fixing errors
            4. Suggestions for improving the application
            5. Next steps for the development team

            Be concise and actionable.
            """
            
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a senior web application developer analyzing test results."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"AI analysis failed: {str(e)}"
    
    def save_report(self, filename: str = None):
        """Save detailed test report to file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"web_app_test_report_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"📄 Report saved to: {filename}")
        return filename

def main():
    """Run the web application tester."""
    print("🚀 Starting Web Application Comprehensive Test")
    print("=" * 50)
    
    tester = WebAppTester()
    
    # Run tests
    results = tester.test_all_pages()
    
    # Get AI analysis
    print(f"\n🤖 Getting AI analysis...")
    ai_analysis = tester.get_ai_analysis()
    
    # Print AI analysis
    print(f"\n🎯 AI Analysis & Recommendations:")
    print("=" * 50)
    print(ai_analysis)
    
    # Save report
    report_file = tester.save_report()
    
    # Final summary
    print(f"\n🏁 Testing Complete!")
    print(f"📊 Success Rate: {results['summary']['success_rate']:.1f}%")
    print(f"📄 Full report: {report_file}")
    
    if results['summary']['failed_pages'] == 0:
        print("🎉 All pages working correctly!")
    else:
        print(f"🔧 {results['summary']['failed_pages']} pages need attention")
    
    return results

if __name__ == "__main__":
    main()