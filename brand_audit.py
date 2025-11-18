#!/usr/bin/env python3
"""
Brand Presence Audit Module
Analyzes Rufus AI responses to audit brand presence (your brands vs competitors).
"""

import json
import re
import logging
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from collections import defaultdict, Counter
from datetime import datetime
import csv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BrandAuditor:
    """Audits brand presence in Rufus AI responses."""
    
    def __init__(self, your_brands: List[str], competitor_brands: List[str]):
        """
        Initialize the brand auditor.
        
        Args:
            your_brands: List of your brand names to track
            competitor_brands: List of competitor brand names to track
        """
        self.your_brands = [brand.lower().strip() for brand in your_brands]
        self.competitor_brands = [brand.lower().strip() for brand in competitor_brands]
        self.all_brands = self.your_brands + self.competitor_brands
        
        # Create case-insensitive regex patterns for each brand
        self.brand_patterns = {}
        for brand in self.all_brands:
            # Escape special regex characters and create word boundary pattern
            escaped_brand = re.escape(brand)
            # Match whole words (case-insensitive)
            pattern = re.compile(r'\b' + escaped_brand + r'\b', re.IGNORECASE)
            self.brand_patterns[brand] = pattern
        
        logger.info(f"Initialized BrandAuditor with {len(self.your_brands)} your brands and {len(self.competitor_brands)} competitor brands")
    
    def find_brand_mentions(self, text: str) -> Dict[str, List[Tuple[int, str]]]:
        """
        Find all brand mentions in text with context.
        
        Args:
            text: Text to search
            
        Returns:
            Dictionary mapping brand names to list of (position, context) tuples
        """
        mentions = defaultdict(list)
        text_lower = text.lower()
        
        for brand, pattern in self.brand_patterns.items():
            for match in pattern.finditer(text):
                start = match.start()
                end = match.end()
                
                # Extract context (50 chars before and after)
                context_start = max(0, start - 50)
                context_end = min(len(text), end + 50)
                context = text[context_start:context_end].strip()
                
                mentions[brand].append((start, context))
        
        return dict(mentions)
    
    def analyze_response(self, response_data: Dict) -> Dict:
        """
        Analyze a single response for brand mentions.
        
        Args:
            response_data: Dictionary containing question, response, etc.
            
        Returns:
            Analysis results dictionary
        """
        question = response_data.get("question", "")
        response_text = response_data.get("response", "")
        timestamp = response_data.get("timestamp", "")
        
        # Combine question and response for analysis
        full_text = f"{question}\n\n{response_text}"
        
        # Find all brand mentions
        mentions = self.find_brand_mentions(full_text)
        
        # Categorize mentions
        your_brand_mentions = {}
        competitor_mentions = {}
        
        for brand, contexts in mentions.items():
            if brand in self.your_brands:
                your_brand_mentions[brand] = contexts
            elif brand in self.competitor_brands:
                competitor_mentions[brand] = contexts
        
        # Count mentions
        your_brand_count = sum(len(contexts) for contexts in your_brand_mentions.values())
        competitor_count = sum(len(contexts) for contexts in competitor_mentions.values())
        total_mentions = your_brand_count + competitor_count
        
        return {
            "question": question,
            "timestamp": timestamp,
            "your_brands_mentioned": list(your_brand_mentions.keys()),
            "competitor_brands_mentioned": list(competitor_mentions.keys()),
            "your_brand_mentions": {brand: len(contexts) for brand, contexts in your_brand_mentions.items()},
            "competitor_mentions": {brand: len(contexts) for brand, contexts in competitor_mentions.items()},
            "your_brand_count": your_brand_count,
            "competitor_count": competitor_count,
            "total_mentions": total_mentions,
            "mentions_with_context": {
                "your_brands": your_brand_mentions,
                "competitors": competitor_mentions
            },
            "has_your_brands": len(your_brand_mentions) > 0,
            "has_competitors": len(competitor_mentions) > 0,
            "response_length": len(response_text)
        }
    
    def audit_responses(self, responses_file: str) -> Dict:
        """
        Audit all responses in a JSON file.
        
        Args:
            responses_file: Path to JSON file containing Rufus responses
            
        Returns:
            Complete audit results
        """
        logger.info(f"Loading responses from {responses_file}")
        
        with open(responses_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        results = data.get("results", [])
        logger.info(f"Analyzing {len(results)} responses...")
        
        # Analyze each response
        response_analyses = []
        for result in results:
            analysis = self.analyze_response(result)
            response_analyses.append(analysis)
        
        # Aggregate statistics
        total_responses = len(response_analyses)
        responses_with_your_brands = sum(1 for a in response_analyses if a["has_your_brands"])
        responses_with_competitors = sum(1 for a in response_analyses if a["has_competitors"])
        responses_with_both = sum(1 for a in response_analyses if a["has_your_brands"] and a["has_competitors"])
        responses_with_neither = sum(1 for a in response_analyses if not a["has_your_brands"] and not a["has_competitors"])
        
        # Brand frequency counts
        your_brand_frequency = Counter()
        competitor_frequency = Counter()
        
        for analysis in response_analyses:
            for brand, count in analysis["your_brand_mentions"].items():
                your_brand_frequency[brand] += count
            for brand, count in analysis["competitor_mentions"].items():
                competitor_frequency[brand] += count
        
        # Calculate presence rates
        your_brand_presence_rate = (responses_with_your_brands / total_responses * 100) if total_responses > 0 else 0
        competitor_presence_rate = (responses_with_competitors / total_responses * 100) if total_responses > 0 else 0
        
        audit_results = {
            "audit_timestamp": datetime.now().isoformat(),
            "source_file": responses_file,
            "summary": {
                "total_responses": total_responses,
                "responses_with_your_brands": responses_with_your_brands,
                "responses_with_competitors": responses_with_competitors,
                "responses_with_both": responses_with_both,
                "responses_with_neither": responses_with_neither,
                "your_brand_presence_rate": round(your_brand_presence_rate, 2),
                "competitor_presence_rate": round(competitor_presence_rate, 2),
                "total_your_brand_mentions": sum(your_brand_frequency.values()),
                "total_competitor_mentions": sum(competitor_frequency.values())
            },
            "brand_statistics": {
                "your_brands": {
                    brand: {
                        "total_mentions": count,
                        "responses_mentioned_in": sum(1 for a in response_analyses if brand in a["your_brands_mentioned"])
                    }
                    for brand, count in your_brand_frequency.items()
                },
                "competitors": {
                    brand: {
                        "total_mentions": count,
                        "responses_mentioned_in": sum(1 for a in response_analyses if brand in a["competitor_brands_mentioned"])
                    }
                    for brand, count in competitor_frequency.items()
                }
            },
            "response_analyses": response_analyses
        }
        
        logger.info(f"Audit complete: {responses_with_your_brands}/{total_responses} responses mention your brands, {responses_with_competitors}/{total_responses} mention competitors")
        
        return audit_results
    
    def save_audit_report(self, audit_results: Dict, output_file: str, format: str = "json"):
        """
        Save audit results to a file.
        
        Args:
            audit_results: Audit results dictionary
            output_file: Output file path
            format: Output format ('json', 'csv', or 'txt')
        """
        output_path = Path(output_file)
        
        if format == "json":
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(audit_results, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved JSON report to {output_path}")
            
        elif format == "csv":
            self._save_csv_report(audit_results, output_path)
            
        elif format == "txt":
            self._save_text_report(audit_results, output_path)
        
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _save_csv_report(self, audit_results: Dict, output_path: Path):
        """Save audit results as CSV."""
        summary = audit_results["summary"]
        brand_stats = audit_results["brand_statistics"]
        response_analyses = audit_results["response_analyses"]
        
        # Summary CSV
        summary_path = output_path.with_suffix('.summary.csv')
        with open(summary_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Metric", "Value"])
            writer.writerow(["Total Responses", summary["total_responses"]])
            writer.writerow(["Responses with Your Brands", summary["responses_with_your_brands"]])
            writer.writerow(["Responses with Competitors", summary["responses_with_competitors"]])
            writer.writerow(["Your Brand Presence Rate (%)", summary["your_brand_presence_rate"]])
            writer.writerow(["Competitor Presence Rate (%)", summary["competitor_presence_rate"]])
            writer.writerow(["Total Your Brand Mentions", summary["total_your_brand_mentions"]])
            writer.writerow(["Total Competitor Mentions", summary["total_competitor_mentions"]])
        
        # Brand statistics CSV
        brand_path = output_path.with_suffix('.brands.csv')
        with open(brand_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Brand", "Type", "Total Mentions", "Responses Mentioned In"])
            
            for brand, stats in brand_stats["your_brands"].items():
                writer.writerow([brand, "Your Brand", stats["total_mentions"], stats["responses_mentioned_in"]])
            
            for brand, stats in brand_stats["competitors"].items():
                writer.writerow([brand, "Competitor", stats["total_mentions"], stats["responses_mentioned_in"]])
        
        # Detailed response analysis CSV
        detail_path = output_path.with_suffix('.detailed.csv')
        with open(detail_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "Question", "Timestamp", "Your Brands Mentioned", "Competitor Brands Mentioned",
                "Your Brand Count", "Competitor Count", "Total Mentions", "Has Your Brands", "Has Competitors"
            ])
            
            for analysis in response_analyses:
                writer.writerow([
                    analysis["question"],
                    analysis["timestamp"],
                    ", ".join(analysis["your_brands_mentioned"]),
                    ", ".join(analysis["competitor_brands_mentioned"]),
                    analysis["your_brand_count"],
                    analysis["competitor_count"],
                    analysis["total_mentions"],
                    analysis["has_your_brands"],
                    analysis["has_competitors"]
                ])
        
        logger.info(f"Saved CSV reports: {summary_path}, {brand_path}, {detail_path}")
    
    def _save_text_report(self, audit_results: Dict, output_path: Path):
        """Save audit results as formatted text report."""
        summary = audit_results["summary"]
        brand_stats = audit_results["brand_statistics"]
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("BRAND PRESENCE AUDIT REPORT\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Audit Date: {audit_results['audit_timestamp']}\n")
            f.write(f"Source File: {audit_results['source_file']}\n\n")
            
            # Summary
            f.write("SUMMARY\n")
            f.write("-" * 80 + "\n")
            f.write(f"Total Responses Analyzed: {summary['total_responses']}\n")
            f.write(f"Responses with Your Brands: {summary['responses_with_your_brands']} ({summary['your_brand_presence_rate']}%)\n")
            f.write(f"Responses with Competitors: {summary['responses_with_competitors']} ({summary['competitor_presence_rate']}%)\n")
            f.write(f"Responses with Both: {summary['responses_with_both']}\n")
            f.write(f"Responses with Neither: {summary['responses_with_neither']}\n")
            f.write(f"Total Your Brand Mentions: {summary['total_your_brand_mentions']}\n")
            f.write(f"Total Competitor Mentions: {summary['total_competitor_mentions']}\n\n")
            
            # Your brands
            f.write("YOUR BRANDS\n")
            f.write("-" * 80 + "\n")
            if brand_stats["your_brands"]:
                for brand, stats in sorted(brand_stats["your_brands"].items(), key=lambda x: x[1]["total_mentions"], reverse=True):
                    f.write(f"  {brand}:\n")
                    f.write(f"    Total Mentions: {stats['total_mentions']}\n")
                    f.write(f"    Responses Mentioned In: {stats['responses_mentioned_in']}\n")
            else:
                f.write("  No mentions found.\n")
            f.write("\n")
            
            # Competitors
            f.write("COMPETITOR BRANDS\n")
            f.write("-" * 80 + "\n")
            if brand_stats["competitors"]:
                for brand, stats in sorted(brand_stats["competitors"].items(), key=lambda x: x[1]["total_mentions"], reverse=True):
                    f.write(f"  {brand}:\n")
                    f.write(f"    Total Mentions: {stats['total_mentions']}\n")
                    f.write(f"    Responses Mentioned In: {stats['responses_mentioned_in']}\n")
            else:
                f.write("  No mentions found.\n")
            f.write("\n")
            
            # Detailed analysis
            f.write("DETAILED RESPONSE ANALYSIS\n")
            f.write("-" * 80 + "\n")
            for i, analysis in enumerate(audit_results["response_analyses"], 1):
                f.write(f"\nResponse {i}:\n")
                f.write(f"  Question: {analysis['question']}\n")
                f.write(f"  Your Brands: {', '.join(analysis['your_brands_mentioned']) if analysis['your_brands_mentioned'] else 'None'}\n")
                f.write(f"  Competitors: {', '.join(analysis['competitor_brands_mentioned']) if analysis['competitor_brands_mentioned'] else 'None'}\n")
                f.write(f"  Mentions: Your={analysis['your_brand_count']}, Competitors={analysis['competitor_count']}\n")
        
        logger.info(f"Saved text report to {output_path}")


def load_brands_from_file(brands_file: str) -> Tuple[List[str], List[str]]:
    """
    Load brands from a JSON file.
    
    Expected format:
    {
        "your_brands": ["Brand1", "Brand2", ...],
        "competitor_brands": ["Competitor1", "Competitor2", ...]
    }
    
    Args:
        brands_file: Path to JSON file
        
    Returns:
        Tuple of (your_brands, competitor_brands)
    """
    with open(brands_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    your_brands = data.get("your_brands", [])
    competitor_brands = data.get("competitor_brands", [])
    
    return your_brands, competitor_brands


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Brand Presence Audit for Rufus AI Responses")
    parser.add_argument("responses_file", help="Path to JSON file containing Rufus responses")
    parser.add_argument("--brands-file", help="JSON file containing brand lists")
    parser.add_argument("--your-brands", nargs="+", help="Your brand names (space-separated)")
    parser.add_argument("--competitor-brands", nargs="+", help="Competitor brand names (space-separated)")
    parser.add_argument("--output", help="Output file path (default: brand_audit_TIMESTAMP.json)")
    parser.add_argument("--format", choices=["json", "csv", "txt", "all"], default="json",
                       help="Output format (default: json)")
    
    args = parser.parse_args()
    
    # Load brands
    if args.brands_file:
        your_brands, competitor_brands = load_brands_from_file(args.brands_file)
        logger.info(f"Loaded {len(your_brands)} your brands and {len(competitor_brands)} competitor brands from file")
    elif args.your_brands and args.competitor_brands:
        your_brands = args.your_brands
        competitor_brands = args.competitor_brands
    else:
        parser.error("Must provide either --brands-file or both --your-brands and --competitor-brands")
    
    if not your_brands and not competitor_brands:
        parser.error("Must provide at least one brand to track")
    
    # Initialize auditor
    auditor = BrandAuditor(your_brands, competitor_brands)
    
    # Run audit
    audit_results = auditor.audit_responses(args.responses_file)
    
    # Determine output file
    if args.output:
        output_file = args.output
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"brand_audit_{timestamp}"
    
    # Save results
    formats = ["json", "csv", "txt"] if args.format == "all" else [args.format]
    for fmt in formats:
        if fmt == "json":
            auditor.save_audit_report(audit_results, f"{output_file}.json", "json")
        elif fmt == "csv":
            auditor.save_audit_report(audit_results, f"{output_file}.csv", "csv")
        elif fmt == "txt":
            auditor.save_audit_report(audit_results, f"{output_file}.txt", "txt")
    
    # Print summary to console
    summary = audit_results["summary"]
    print("\n" + "=" * 80)
    print("AUDIT SUMMARY")
    print("=" * 80)
    print(f"Total Responses: {summary['total_responses']}")
    print(f"Your Brand Presence: {summary['responses_with_your_brands']}/{summary['total_responses']} ({summary['your_brand_presence_rate']}%)")
    print(f"Competitor Presence: {summary['responses_with_competitors']}/{summary['total_responses']} ({summary['competitor_presence_rate']}%)")
    print(f"Total Your Brand Mentions: {summary['total_your_brand_mentions']}")
    print(f"Total Competitor Mentions: {summary['total_competitor_mentions']}")
    print("=" * 80)


if __name__ == "__main__":
    main()

