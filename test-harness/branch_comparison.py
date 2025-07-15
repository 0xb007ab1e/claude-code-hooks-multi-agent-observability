#!/usr/bin/env python3
"""
Branch Comparison Test System
This script tests different server branches and compares results to ensure parity.
"""

import os
import sys
import subprocess
import time
import json
import argparse
from datetime import datetime
from typing import Dict, List, Optional
import requests
from utils.docker_utils import docker_manager
from config.test_config import config
from config.port_manager import get_port, assign_port

class BranchComparison:
    """Compare test results across different server branches."""
    
    def __init__(self):
        self.comparison_results = {}
        self.baseline_results = None
        
    def get_git_branches(self) -> List[str]:
        """Get list of git branches."""
        try:
            result = subprocess.run(['git', 'branch', '-r'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                branches = []
                for line in result.stdout.strip().split('\n'):
                    branch = line.strip().replace('origin/', '')
                    if branch and not branch.startswith('HEAD'):
                        branches.append(branch)
                return branches
        except Exception as e:
            print(f"Error getting git branches: {e}")
        return []
    
    def checkout_branch(self, branch: str) -> bool:
        """Checkout a specific git branch."""
        try:
            result = subprocess.run(['git', 'checkout', branch], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            print(f"Error checking out branch {branch}: {e}")
            return False
    
    def build_server_image(self, branch: str) -> str:
        """Build server image for a specific branch."""
        image_name = f"multi-agent-server:{branch}"
        
        # Build the image
        try:
            result = subprocess.run([
                'docker', 'build', 
                '-t', image_name, 
                '-f', '../apps/server/Dockerfile',
                '../apps/server'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Built image: {image_name}")
                return image_name
            else:
                print(f"❌ Failed to build image for branch {branch}")
                print(result.stderr)
                return None
        except Exception as e:
            print(f"Error building image for branch {branch}: {e}")
            return None
    
    def start_server_container(self, image: str) -> str:
        """Start server container."""
        container_name = f"test-server-{int(time.time())}"
        
        try:
            result = subprocess.run([
                'docker', 'run', '-d', 
                '--name', container_name,
                '-p', f'{get_port("http-server") or assign_port("http-server", "Main HTTP Server")}:{get_port("http-server") or assign_port("http-server", "Main HTTP Server")}',
                image
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                container_id = result.stdout.strip()
                print(f"✅ Started container: {container_name}")
                return container_id
            else:
                print(f"❌ Failed to start container from image {image}")
                print(result.stderr)
                return None
        except Exception as e:
            print(f"Error starting container: {e}")
            return None
    
    def stop_container(self, container_id: str):
        """Stop and remove container."""
        try:
            subprocess.run(['docker', 'stop', container_id], 
                          capture_output=True, text=True)
            subprocess.run(['docker', 'rm', container_id], 
                          capture_output=True, text=True)
            print(f"✅ Stopped and removed container: {container_id}")
        except Exception as e:
            print(f"Error stopping container: {e}")
    
    def run_tests_for_branch(self, branch: str) -> Dict:
        """Run tests for a specific branch."""
        print(f"\\n🌿 Testing branch: {branch}")
        print("="*50)
        
        # Checkout branch
        if not self.checkout_branch(branch):
            return {"error": f"Failed to checkout branch {branch}"}
        
        # Build server image
        image = self.build_server_image(branch)
        if not image:
            return {"error": f"Failed to build image for branch {branch}"}
        
        # Start container
        container_id = self.start_server_container(image)
        if not container_id:
            return {"error": f"Failed to start container for branch {branch}"}
        
        try:
            # Wait for server to be ready
            if not self.wait_for_server():
                return {"error": f"Server not ready for branch {branch}"}
            
            # Run tests
            from run_e2e_tests import E2ETestRunner
            runner = E2ETestRunner(server_image=image, branch=branch)
            runner.run_all_tests()
            
            results = runner.generate_summary_report()
            results["branch"] = branch
            results["image"] = image
            
            return results
            
        finally:
            # Always stop the container
            self.stop_container(container_id)
    
    def wait_for_server(self, max_wait: int = 60) -> bool:
        """Wait for server to be ready."""
        print(f"Waiting for server at {config.server.base_url}...")
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                response = requests.get(config.server.base_url, timeout=5)
                if response.status_code == 200:
                    print("✅ Server is ready!")
                    return True
            except requests.exceptions.RequestException:
                pass
            time.sleep(2)
        
        print("❌ Server failed to start within timeout")
        return False
    
    def compare_branches(self, branches: List[str], baseline: str = None) -> Dict:
        """Compare test results across branches."""
        if baseline:
            branches = [baseline] + [b for b in branches if b != baseline]
        
        comparison_results = {}
        
        for branch in branches:
            result = self.run_tests_for_branch(branch)
            comparison_results[branch] = result
            
            # Set baseline if this is the first branch
            if baseline == branch or (baseline is None and self.baseline_results is None):
                self.baseline_results = result
                print(f"📊 Set {branch} as baseline")
        
        self.comparison_results = comparison_results
        return comparison_results
    
    def analyze_differences(self) -> Dict:
        """Analyze differences between branches."""
        if not self.baseline_results or not self.comparison_results:
            return {"error": "No comparison data available"}
        
        analysis = {
            "baseline_branch": self.baseline_results.get("branch"),
            "baseline_success_rate": self.baseline_results.get("success_rate"),
            "comparisons": {}
        }
        
        for branch, results in self.comparison_results.items():
            if branch == self.baseline_results.get("branch"):
                continue
            
            if "error" in results:
                analysis["comparisons"][branch] = {
                    "status": "error",
                    "error": results["error"]
                }
                continue
            
            success_rate = results.get("success_rate", 0)
            baseline_rate = self.baseline_results.get("success_rate", 0)
            
            # Compare success rates
            rate_diff = success_rate - baseline_rate
            
            # Compare test results
            parity_issues = []
            baseline_suite_results = {
                name: result["success"] 
                for name, result in self.baseline_results.get("results", {}).items()
            }
            
            branch_suite_results = {
                name: result["success"] 
                for name, result in results.get("results", {}).items()
            }
            
            for suite_name, baseline_success in baseline_suite_results.items():
                branch_success = branch_suite_results.get(suite_name, False)
                if baseline_success != branch_success:
                    parity_issues.append({
                        "suite": suite_name,
                        "baseline": baseline_success,
                        "branch": branch_success,
                        "impact": "regression" if baseline_success and not branch_success else "improvement"
                    })
            
            analysis["comparisons"][branch] = {
                "status": "compared",
                "success_rate": success_rate,
                "rate_difference": rate_diff,
                "parity_maintained": len(parity_issues) == 0,
                "parity_issues": parity_issues,
                "duration": results.get("duration", 0)
            }
        
        return analysis
    
    def generate_report(self, output_file: str = None) -> str:
        """Generate comparison report."""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"reports/branch_comparison_{timestamp}.json"
        
        os.makedirs("reports", exist_ok=True)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "comparison_results": self.comparison_results,
            "analysis": self.analyze_differences()
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📊 Comparison report saved to {output_file}")
        return output_file
    
    def print_summary(self):
        """Print comparison summary."""
        analysis = self.analyze_differences()
        
        print("\\n" + "="*60)
        print("🔍 Branch Comparison Summary")
        print("="*60)
        
        if "error" in analysis:
            print(f"❌ Error: {analysis['error']}")
            return
        
        print(f"📊 Baseline: {analysis['baseline_branch']} ({analysis['baseline_success_rate']:.1f}%)")
        
        for branch, comparison in analysis["comparisons"].items():
            if comparison["status"] == "error":
                print(f"❌ {branch}: {comparison['error']}")
            else:
                status_icon = "✅" if comparison["parity_maintained"] else "⚠️"
                rate_change = comparison["rate_difference"]
                rate_icon = "📈" if rate_change > 0 else "📉" if rate_change < 0 else "➡️"
                
                print(f"{status_icon} {branch}: {comparison['success_rate']:.1f}% {rate_icon} ({rate_change:+.1f}%)")
                
                if not comparison["parity_maintained"]:
                    for issue in comparison["parity_issues"]:
                        impact_icon = "🔴" if issue["impact"] == "regression" else "🟢"
                        print(f"    {impact_icon} {issue['suite']}: {issue['baseline']} → {issue['branch']}")
        
        print("="*60)

def main():
    parser = argparse.ArgumentParser(description="Compare test results across server branches")
    parser.add_argument("--branches", nargs='+', help="Specific branches to test")
    parser.add_argument("--baseline", help="Baseline branch for comparison")
    parser.add_argument("--output", help="Output file for comparison report")
    parser.add_argument("--auto-discover", action="store_true", help="Auto-discover git branches")
    
    args = parser.parse_args()
    
    comparator = BranchComparison()
    
    # Determine branches to test
    if args.branches:
        branches = args.branches
    elif args.auto_discover:
        branches = comparator.get_git_branches()
        print(f"🔍 Discovered branches: {branches}")
    else:
        print("❌ No branches specified. Use --branches or --auto-discover")
        sys.exit(1)
    
    if not branches:
        print("❌ No branches to test")
        sys.exit(1)
    
    # Run comparison
    print(f"🚀 Starting branch comparison for: {branches}")
    comparator.compare_branches(branches, baseline=args.baseline)
    
    # Generate report
    comparator.generate_report(args.output)
    comparator.print_summary()

if __name__ == "__main__":
    main()
