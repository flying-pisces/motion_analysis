#!/usr/bin/env python3
"""
Batch Video Analyzer
Processes multiple video recordings and generates comprehensive delta analysis.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import numpy as np
from collections import defaultdict, Counter
import matplotlib.pyplot as plt
import seaborn as sns


class BatchVideoAnalyzer:
    """Analyze multiple video recordings for patterns and deltas."""

    def __init__(self, recordings_dir: str, instruction_json: str, output_dir: str = None):
        """Initialize batch analyzer."""
        self.recordings_dir = Path(recordings_dir)
        self.instruction_json = instruction_json

        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = self.recordings_dir / 'batch_analysis'

        self.output_dir.mkdir(exist_ok=True)

        # Results storage
        self.video_analyses = {}
        self.batch_statistics = {}
        self.patterns = {}
        self.anomalies = []

    def get_substantial_videos(self, min_size_mb: float = 5.0) -> List[Path]:
        """Get list of substantial video files (not empty/corrupted)."""
        videos = []
        min_bytes = min_size_mb * 1024 * 1024

        for video_file in self.recordings_dir.glob("*.mp4"):
            if video_file.stat().st_size > min_bytes:
                videos.append(video_file)

        # Sort by timestamp (extracted from filename)
        videos.sort(key=lambda x: x.name)
        return videos

    def analyze_single_video(self, video_path: Path) -> Dict:
        """Analyze a single video using the instruction analyzer."""
        print(f"Analyzing: {video_path.name}")

        # Create temporary output directory for this video
        temp_output = self.output_dir / f"temp_{video_path.stem}"
        temp_output.mkdir(exist_ok=True)

        try:
            # Import and use the instruction analyzer
            sys.path.append(str(Path(__file__).parent))
            from instruction_analyzer import analyze_instruction_and_video

            # Analyze this video
            results = analyze_instruction_and_video(
                self.instruction_json,
                str(video_path),
                str(temp_output)
            )

            return {
                'video_path': str(video_path),
                'analysis_successful': True,
                'results': results,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            print(f"  Error analyzing {video_path.name}: {e}")
            return {
                'video_path': str(video_path),
                'analysis_successful': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def analyze_all_videos(self, max_videos: int = 20) -> Dict:
        """Analyze multiple videos in batch."""
        print(f"\n=== Batch Video Analysis ===")

        videos = self.get_substantial_videos()
        print(f"Found {len(videos)} substantial videos")

        # Limit the number of videos to analyze
        if len(videos) > max_videos:
            print(f"Limiting to first {max_videos} videos for analysis")
            videos = videos[:max_videos]

        # Analyze each video
        for i, video_path in enumerate(videos, 1):
            print(f"\n[{i}/{len(videos)}] ", end="")
            analysis = self.analyze_single_video(video_path)
            self.video_analyses[video_path.name] = analysis

        print(f"\n✅ Batch analysis complete!")
        return self.video_analyses

    def extract_patterns(self) -> Dict:
        """Extract patterns from multiple video analyses."""
        patterns = {
            'duration_patterns': {},
            'activity_patterns': {},
            'timing_consistency': {},
            'coverage_patterns': {}
        }

        # Collect data from successful analyses
        successful_analyses = [
            analysis for analysis in self.video_analyses.values()
            if analysis['analysis_successful']
        ]

        if not successful_analyses:
            return patterns

        # Duration patterns
        durations = []
        activity_counts = []
        coverage_percentages = []

        for analysis in successful_analyses:
            try:
                video_analysis = analysis['results']['video_analysis']
                durations.append(video_analysis['duration'])
                activity_counts.append(len(video_analysis['activity_periods']))

                # Calculate coverage
                instruction_analysis = analysis['results']['instruction_analysis']
                total_steps = instruction_analysis['summary']['total_steps']
                activity_periods = len(video_analysis['activity_periods'])
                coverage = min(activity_periods / total_steps, 1.0) if total_steps > 0 else 0
                coverage_percentages.append(coverage * 100)

            except (KeyError, TypeError, ZeroDivisionError):
                continue

        # Calculate statistics
        if durations:
            patterns['duration_patterns'] = {
                'mean': float(np.mean(durations)),
                'std': float(np.std(durations)),
                'min': float(np.min(durations)),
                'max': float(np.max(durations)),
                'median': float(np.median(durations))
            }

        if activity_counts:
            patterns['activity_patterns'] = {
                'mean_activities': float(np.mean(activity_counts)),
                'std_activities': float(np.std(activity_counts)),
                'mode_activities': int(Counter(activity_counts).most_common(1)[0][0]) if activity_counts else 0
            }

        if coverage_percentages:
            patterns['coverage_patterns'] = {
                'mean_coverage': float(np.mean(coverage_percentages)),
                'std_coverage': float(np.std(coverage_percentages)),
                'min_coverage': float(np.min(coverage_percentages)),
                'max_coverage': float(np.max(coverage_percentages))
            }

        self.patterns = patterns
        return patterns

    def identify_anomalies(self) -> List[Dict]:
        """Identify anomalous recordings based on patterns."""
        anomalies = []

        if not self.patterns:
            self.extract_patterns()

        # Duration anomalies
        if 'duration_patterns' in self.patterns:
            mean_duration = self.patterns['duration_patterns']['mean']
            std_duration = self.patterns['duration_patterns']['std']

            for video_name, analysis in self.video_analyses.items():
                if not analysis['analysis_successful']:
                    continue

                try:
                    duration = analysis['results']['video_analysis']['duration']

                    # Check for outliers (more than 2 standard deviations from mean)
                    if abs(duration - mean_duration) > 2 * std_duration:
                        anomalies.append({
                            'video': video_name,
                            'type': 'duration_anomaly',
                            'value': duration,
                            'expected_range': f"{mean_duration - 2*std_duration:.1f} - {mean_duration + 2*std_duration:.1f}",
                            'severity': 'high' if abs(duration - mean_duration) > 3 * std_duration else 'medium'
                        })

                except (KeyError, TypeError):
                    continue

        # Coverage anomalies
        if 'coverage_patterns' in self.patterns:
            mean_coverage = self.patterns['coverage_patterns']['mean_coverage']

            for video_name, analysis in self.video_analyses.items():
                if not analysis['analysis_successful']:
                    continue

                try:
                    instruction_analysis = analysis['results']['instruction_analysis']
                    video_analysis = analysis['results']['video_analysis']

                    total_steps = instruction_analysis['summary']['total_steps']
                    activity_periods = len(video_analysis['activity_periods'])
                    coverage = min(activity_periods / total_steps, 1.0) * 100 if total_steps > 0 else 0

                    # Check for very low coverage
                    if coverage < mean_coverage * 0.5:  # Less than 50% of average
                        anomalies.append({
                            'video': video_name,
                            'type': 'low_coverage',
                            'value': coverage,
                            'expected': mean_coverage,
                            'severity': 'high' if coverage < 10 else 'medium'
                        })

                except (KeyError, TypeError, ZeroDivisionError):
                    continue

        self.anomalies = anomalies
        return anomalies

    def generate_comprehensive_report(self) -> str:
        """Generate comprehensive delta analysis report."""
        report_lines = []

        report_lines.append("# Comprehensive Video Recording Analysis Report")
        report_lines.append("")
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report_lines.append("")

        # Summary statistics
        successful_count = sum(1 for a in self.video_analyses.values() if a['analysis_successful'])
        total_count = len(self.video_analyses)

        report_lines.append("## Executive Summary")
        report_lines.append(f"- **Total Videos Analyzed**: {total_count}")
        report_lines.append(f"- **Successful Analyses**: {successful_count}")
        report_lines.append(f"- **Success Rate**: {(successful_count/total_count)*100:.1f}%")
        report_lines.append("")

        # Patterns
        if self.patterns:
            report_lines.append("## Identified Patterns")

            if 'duration_patterns' in self.patterns:
                dp = self.patterns['duration_patterns']
                report_lines.append("### Duration Patterns")
                report_lines.append(f"- **Average Duration**: {dp['mean']:.1f} ± {dp['std']:.1f} seconds")
                report_lines.append(f"- **Range**: {dp['min']:.1f} - {dp['max']:.1f} seconds")
                report_lines.append(f"- **Median**: {dp['median']:.1f} seconds")
                report_lines.append("")

            if 'coverage_patterns' in self.patterns:
                cp = self.patterns['coverage_patterns']
                report_lines.append("### Coverage Patterns")
                report_lines.append(f"- **Average Coverage**: {cp['mean_coverage']:.1f}%")
                report_lines.append(f"- **Coverage Range**: {cp['min_coverage']:.1f}% - {cp['max_coverage']:.1f}%")
                report_lines.append(f"- **Coverage Consistency**: ±{cp['std_coverage']:.1f}%")
                report_lines.append("")

        # Anomalies
        if self.anomalies:
            report_lines.append("## Identified Anomalies")

            high_severity = [a for a in self.anomalies if a['severity'] == 'high']
            medium_severity = [a for a in self.anomalies if a['severity'] == 'medium']

            if high_severity:
                report_lines.append("### High Severity Issues")
                for anomaly in high_severity:
                    report_lines.append(f"- **{anomaly['video']}**: {anomaly['type']} - {anomaly['value']:.1f}")
                report_lines.append("")

            if medium_severity:
                report_lines.append("### Medium Severity Issues")
                for anomaly in medium_severity:
                    report_lines.append(f"- **{anomaly['video']}**: {anomaly['type']} - {anomaly['value']:.1f}")
                report_lines.append("")

        # Detailed video analysis
        report_lines.append("## Detailed Video Analysis")
        for video_name, analysis in self.video_analyses.items():
            report_lines.append(f"### {video_name}")

            if analysis['analysis_successful']:
                try:
                    video_analysis = analysis['results']['video_analysis']
                    instruction_analysis = analysis['results']['instruction_analysis']

                    duration = video_analysis['duration']
                    activity_periods = len(video_analysis['activity_periods'])
                    total_steps = instruction_analysis['summary']['total_steps']
                    coverage = min(activity_periods / total_steps, 1.0) * 100 if total_steps > 0 else 0

                    report_lines.append(f"- **Duration**: {duration:.1f} seconds")
                    report_lines.append(f"- **Activity Periods**: {activity_periods}")
                    report_lines.append(f"- **Coverage**: {coverage:.1f}%")
                    report_lines.append(f"- **Status**: ✅ Analyzed successfully")

                except (KeyError, TypeError):
                    report_lines.append("- **Status**: ⚠️ Analysis incomplete")
            else:
                report_lines.append(f"- **Status**: ❌ Analysis failed - {analysis.get('error', 'Unknown error')}")

            report_lines.append("")

        # Recommendations
        report_lines.append("## Recommendations")

        if self.anomalies:
            high_anomalies = [a for a in self.anomalies if a['severity'] == 'high']
            if high_anomalies:
                report_lines.append("### Immediate Actions Required")
                for anomaly in high_anomalies:
                    if anomaly['type'] == 'low_coverage':
                        report_lines.append(f"- Re-record {anomaly['video']} - insufficient coverage ({anomaly['value']:.1f}%)")
                    elif anomaly['type'] == 'duration_anomaly':
                        report_lines.append(f"- Review {anomaly['video']} - unusual duration ({anomaly['value']:.1f}s)")
                report_lines.append("")

        if 'coverage_patterns' in self.patterns:
            avg_coverage = self.patterns['coverage_patterns']['mean_coverage']
            if avg_coverage < 50:
                report_lines.append("### Coverage Improvement")
                report_lines.append(f"- Overall coverage is low ({avg_coverage:.1f}%)")
                report_lines.append("- Consider recording longer sessions to capture more assembly steps")
                report_lines.append("- Ensure all instruction steps are being followed during recording")
                report_lines.append("")

        report_lines.append("### Quality Assurance")
        report_lines.append("- Implement consistent recording procedures")
        report_lines.append("- Use standardized timing for each assembly step")
        report_lines.append("- Validate recordings before processing")
        report_lines.append("")

        return '\n'.join(report_lines)

    def save_results(self):
        """Save all analysis results."""
        # Save batch analysis data
        with open(self.output_dir / 'batch_analysis.json', 'w') as f:
            json.dump({
                'video_analyses': self.video_analyses,
                'patterns': self.patterns,
                'anomalies': self.anomalies,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2, default=str)

        # Save comprehensive report
        report = self.generate_comprehensive_report()
        with open(self.output_dir / 'comprehensive_report.md', 'w') as f:
            f.write(report)

        print(f"📁 Batch analysis results saved to: {self.output_dir}")


def main():
    """Main function for command-line usage."""
    if len(sys.argv) < 3:
        print("Usage: python batch_analyzer.py <recordings_dir> <instruction_json> [output_dir] [max_videos]")
        sys.exit(1)

    recordings_dir = sys.argv[1]
    instruction_json = sys.argv[2]
    output_dir = sys.argv[3] if len(sys.argv) > 3 else None
    max_videos = int(sys.argv[4]) if len(sys.argv) > 4 else 10

    # Run batch analysis
    analyzer = BatchVideoAnalyzer(recordings_dir, instruction_json, output_dir)
    analyzer.analyze_all_videos(max_videos)
    analyzer.extract_patterns()
    analyzer.identify_anomalies()
    analyzer.save_results()

    return analyzer


if __name__ == "__main__":
    main()