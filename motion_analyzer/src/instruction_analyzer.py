#!/usr/bin/env python3
"""
Instruction Analyzer and Video Comparison Tool
Analyzes instructions and compares them with recorded videos to find deltas.
"""

import os
import sys
import json
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import re
from collections import defaultdict
import hashlib


class InstructionAnalyzer:
    """Analyze instructions and extract actionable steps."""

    def __init__(self, json_file: str):
        """Initialize with instruction JSON file."""
        self.json_file = Path(json_file)

        with open(json_file, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

        self.instructions = []
        self.parts_list = []
        self.tools_required = []
        self.assembly_steps = []
        self.test_procedures = []

    def extract_parts_list(self) -> List[Dict]:
        """Extract parts list from instruction slides."""
        parts = []

        for slide in self.data['slides']:
            # Look for tables that contain part numbers
            if slide.get('tables'):
                for table in slide['tables']:
                    content = table['content']
                    # Check if this looks like a parts table
                    if any(pattern in content for pattern in ['M-', 'P-', 'F-', 'CONF']):
                        lines = content.split('\n')
                        for line in lines[2:]:  # Skip header and separator
                            if '|' in line:
                                cells = [c.strip() for c in line.split('|')[1:-1]]
                                if len(cells) >= 2:
                                    part_num = cells[0].strip()
                                    if re.match(r'[A-Z]-\d+', part_num) or 'CONF' in part_num:
                                        parts.append({
                                            'part_number': part_num,
                                            'description': cells[1] if len(cells) > 1 else '',
                                            'quantity': cells[2] if len(cells) > 2 else '1',
                                            'slide': slide['slide_number']
                                        })

        return parts

    def extract_assembly_steps(self) -> List[Dict]:
        """Extract assembly steps from instruction content."""
        steps = []
        step_number = 0

        for slide in self.data['slides']:
            # Check if this slide contains assembly instructions
            if slide.get('title') and 'Mount' in slide.get('title', ''):
                step_number += 1
                step = {
                    'step_number': step_number,
                    'slide_number': slide['slide_number'],
                    'title': slide['title'],
                    'actions': [],
                    'parts_used': [],
                    'tools_used': [],
                    'images': slide.get('images', [])
                }

                # Extract actions from content
                if slide.get('content'):
                    for item in slide['content']:
                        content_text = item['content']

                        # Extract part numbers mentioned
                        part_matches = re.findall(r'\[([A-Z]-\d+[A-Z0-9-]*)\]', content_text)
                        step['parts_used'].extend(part_matches)

                        # Extract tool references (F- parts are fasteners/tools)
                        tool_matches = re.findall(r'F-\d+[A-Z0-9-]*', content_text)
                        step['tools_used'].extend(tool_matches)

                        # Extract actions (verbs)
                        action_words = ['Mount', 'Fasten', 'Use', 'Add', 'Place', 'Install', 'Connect']
                        for action in action_words:
                            if action in content_text:
                                step['actions'].append(content_text)
                                break

                steps.append(step)

        return steps

    def extract_test_procedures(self) -> List[Dict]:
        """Extract test procedures from instructions."""
        tests = []

        for slide in self.data['slides']:
            title = slide.get('title', '').lower()

            # Check for test-related slides
            if any(word in title for word in ['test', 'calibration', 'cogging', 'thermal', 'stress']):
                test = {
                    'slide_number': slide['slide_number'],
                    'test_name': slide['title'],
                    'procedure': [],
                    'expected_results': []
                }

                # Extract procedure from content
                if slide.get('content'):
                    for item in slide['content']:
                        test['procedure'].append(item['content'])

                # Extract from tables if present
                if slide.get('tables'):
                    for table in slide['tables']:
                        test['expected_results'].append(table['content'])

                tests.append(test)

        return tests

    def analyze(self) -> Dict:
        """Perform complete analysis of instructions."""
        print("Analyzing instructions...")

        self.parts_list = self.extract_parts_list()
        self.assembly_steps = self.extract_assembly_steps()
        self.test_procedures = self.extract_test_procedures()

        # Extract unique tools
        all_tools = set()
        for step in self.assembly_steps:
            all_tools.update(step['tools_used'])
        self.tools_required = list(all_tools)

        analysis = {
            'metadata': self.data['metadata'],
            'summary': {
                'total_slides': len(self.data['slides']),
                'total_parts': len(self.parts_list),
                'total_steps': len(self.assembly_steps),
                'total_tests': len(self.test_procedures),
                'tools_required': len(self.tools_required)
            },
            'parts_list': self.parts_list,
            'assembly_steps': self.assembly_steps,
            'test_procedures': self.test_procedures,
            'tools_required': self.tools_required
        }

        return analysis

    def generate_checklist(self) -> str:
        """Generate a checklist from the instructions."""
        checklist_lines = []

        checklist_lines.append(f"# Assembly Checklist: {self.data['metadata']['title']}")
        checklist_lines.append("")
        checklist_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        checklist_lines.append("")

        # Parts checklist
        checklist_lines.append("## Parts Required")
        for part in self.parts_list:
            checklist_lines.append(f"- [ ] {part['part_number']}: {part['description']} (Qty: {part['quantity']})")
        checklist_lines.append("")

        # Tools checklist
        checklist_lines.append("## Tools Required")
        for tool in self.tools_required:
            checklist_lines.append(f"- [ ] {tool}")
        checklist_lines.append("")

        # Assembly steps checklist
        checklist_lines.append("## Assembly Steps")
        for step in self.assembly_steps:
            checklist_lines.append(f"### Step {step['step_number']}: {step['title']}")
            for action in step['actions']:
                checklist_lines.append(f"- [ ] {action}")
            checklist_lines.append("")

        # Test procedures checklist
        checklist_lines.append("## Test Procedures")
        for test in self.test_procedures:
            checklist_lines.append(f"### {test['test_name']}")
            for proc in test['procedure']:
                checklist_lines.append(f"- [ ] {proc}")
            checklist_lines.append("")

        return '\n'.join(checklist_lines)


class VideoRecordingAnalyzer:
    """Analyze video recordings for motion and actions."""

    def __init__(self, video_path: str):
        """Initialize with video file path."""
        self.video_path = Path(video_path)
        self.cap = cv2.VideoCapture(str(video_path))

        # Video properties
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.duration = self.frame_count / self.fps if self.fps > 0 else 0

        # Analysis results
        self.motion_events = []
        self.activity_periods = []
        self.key_frames = []

    def detect_motion_events(self, sample_rate: int = 30) -> List[Dict]:
        """Detect motion events in the video."""
        print(f"Analyzing video: {self.video_path.name}")

        events = []
        prev_frame = None
        frame_idx = 0

        while True:
            # Sample frames at specified rate
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = self.cap.read()

            if not ret:
                break

            # Convert to grayscale for motion detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            if prev_frame is not None:
                # Calculate frame difference
                diff = cv2.absdiff(prev_frame, gray)
                motion_score = np.mean(diff)

                # Detect significant motion
                if motion_score > 10:  # Threshold for motion detection
                    timestamp = frame_idx / self.fps
                    events.append({
                        'frame': frame_idx,
                        'timestamp': timestamp,
                        'time_str': str(timedelta(seconds=int(timestamp))),
                        'motion_score': float(motion_score),
                        'type': 'high_motion' if motion_score > 30 else 'moderate_motion'
                    })

            prev_frame = gray
            frame_idx += sample_rate

            # Progress indicator
            if frame_idx % (sample_rate * 10) == 0:
                progress = (frame_idx / self.frame_count) * 100
                print(f"  Progress: {progress:.1f}%", end='\r')

        print(f"  Found {len(events)} motion events")
        self.motion_events = events
        return events

    def identify_activity_periods(self) -> List[Dict]:
        """Identify continuous activity periods."""
        if not self.motion_events:
            return []

        periods = []
        current_period = None

        for event in self.motion_events:
            if current_period is None:
                # Start new period
                current_period = {
                    'start_time': event['timestamp'],
                    'end_time': event['timestamp'],
                    'duration': 0,
                    'events': [event]
                }
            elif event['timestamp'] - current_period['end_time'] < 5:  # Within 5 seconds
                # Continue current period
                current_period['end_time'] = event['timestamp']
                current_period['events'].append(event)
            else:
                # End current period and start new
                current_period['duration'] = current_period['end_time'] - current_period['start_time']
                if current_period['duration'] > 2:  # Minimum 2 seconds
                    periods.append(current_period)

                current_period = {
                    'start_time': event['timestamp'],
                    'end_time': event['timestamp'],
                    'duration': 0,
                    'events': [event]
                }

        # Add last period
        if current_period and current_period['duration'] > 2:
            periods.append(current_period)

        self.activity_periods = periods
        return periods

    def extract_key_frames(self, max_frames: int = 10) -> List[Dict]:
        """Extract key frames from high motion events."""
        key_frames = []

        # Select frames with highest motion scores
        sorted_events = sorted(self.motion_events, key=lambda x: x['motion_score'], reverse=True)

        for event in sorted_events[:max_frames]:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, event['frame'])
            ret, frame = self.cap.read()

            if ret:
                # Save frame as image
                frame_filename = f"keyframe_{event['frame']:06d}.jpg"
                frame_path = self.video_path.parent / 'keyframes' / frame_filename
                frame_path.parent.mkdir(exist_ok=True)

                cv2.imwrite(str(frame_path), frame)

                key_frames.append({
                    'frame': event['frame'],
                    'timestamp': event['timestamp'],
                    'motion_score': event['motion_score'],
                    'image_path': str(frame_path)
                })

        self.key_frames = key_frames
        return key_frames

    def close(self):
        """Release video capture."""
        self.cap.release()


class InstructionVideoComparator:
    """Compare instructions with video recordings to find deltas."""

    def __init__(self, instruction_analysis: Dict, video_analysis: Dict):
        """Initialize with analyzed instruction and video data."""
        self.instruction_analysis = instruction_analysis
        self.video_analysis = video_analysis
        self.comparison_results = {}

    def estimate_step_timing(self) -> List[Dict]:
        """Estimate which video periods correspond to instruction steps."""
        estimated_steps = []

        # Get activity periods from video
        activity_periods = self.video_analysis.get('activity_periods', [])
        assembly_steps = self.instruction_analysis.get('assembly_steps', [])

        # Simple heuristic: map activity periods to steps sequentially
        for i, period in enumerate(activity_periods):
            if i < len(assembly_steps):
                step = assembly_steps[i]
                estimated_steps.append({
                    'instruction_step': step['step_number'],
                    'instruction_title': step['title'],
                    'video_start': period['start_time'],
                    'video_end': period['end_time'],
                    'duration': period['duration'],
                    'confidence': 'low'  # Since this is just estimation
                })

        return estimated_steps

    def analyze_coverage(self) -> Dict:
        """Analyze how well the video covers the instructions."""
        assembly_steps = self.instruction_analysis.get('assembly_steps', [])
        activity_periods = self.video_analysis.get('activity_periods', [])

        coverage = {
            'total_instruction_steps': len(assembly_steps),
            'total_activity_periods': len(activity_periods),
            'estimated_coverage': min(len(activity_periods) / len(assembly_steps), 1.0) if assembly_steps else 0,
            'missing_steps': max(0, len(assembly_steps) - len(activity_periods))
        }

        return coverage

    def identify_deltas(self) -> Dict:
        """Identify differences between instructions and video."""
        deltas = {
            'timing_deltas': [],
            'coverage_deltas': [],
            'sequence_deltas': []
        }

        # Timing analysis
        estimated_steps = self.estimate_step_timing()
        for step in estimated_steps:
            if step['duration'] < 10:  # Too short
                deltas['timing_deltas'].append({
                    'step': step['instruction_step'],
                    'issue': 'Step completed too quickly',
                    'expected_min': 10,
                    'actual': step['duration']
                })
            elif step['duration'] > 300:  # Too long (5 minutes)
                deltas['timing_deltas'].append({
                    'step': step['instruction_step'],
                    'issue': 'Step took too long',
                    'expected_max': 300,
                    'actual': step['duration']
                })

        # Coverage analysis
        coverage = self.analyze_coverage()
        if coverage['missing_steps'] > 0:
            deltas['coverage_deltas'].append({
                'issue': 'Incomplete coverage',
                'missing_steps': coverage['missing_steps'],
                'coverage_percentage': coverage['estimated_coverage'] * 100
            })

        return deltas

    def generate_comparison_report(self) -> str:
        """Generate a detailed comparison report."""
        report_lines = []

        report_lines.append("# Instruction vs Video Comparison Report")
        report_lines.append("")
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report_lines.append("")

        # Summary
        report_lines.append("## Summary")
        coverage = self.analyze_coverage()
        report_lines.append(f"- Instruction Steps: {coverage['total_instruction_steps']}")
        report_lines.append(f"- Video Activity Periods: {coverage['total_activity_periods']}")
        report_lines.append(f"- Estimated Coverage: {coverage['estimated_coverage']*100:.1f}%")
        report_lines.append("")

        # Estimated Step Mapping
        report_lines.append("## Estimated Step Mapping")
        estimated_steps = self.estimate_step_timing()
        for step in estimated_steps:
            report_lines.append(f"- **Step {step['instruction_step']}**: {step['instruction_title']}")
            report_lines.append(f"  - Video Time: {step['video_start']:.1f}s - {step['video_end']:.1f}s")
            report_lines.append(f"  - Duration: {step['duration']:.1f}s")
            report_lines.append("")

        # Deltas
        report_lines.append("## Identified Deltas")
        deltas = self.identify_deltas()

        if deltas['timing_deltas']:
            report_lines.append("### Timing Issues")
            for delta in deltas['timing_deltas']:
                report_lines.append(f"- Step {delta['step']}: {delta['issue']} ({delta['actual']:.1f}s)")
            report_lines.append("")

        if deltas['coverage_deltas']:
            report_lines.append("### Coverage Issues")
            for delta in deltas['coverage_deltas']:
                report_lines.append(f"- {delta['issue']}: {delta['coverage_percentage']:.1f}% coverage")
            report_lines.append("")

        # Recommendations
        report_lines.append("## Recommendations")
        if coverage['missing_steps'] > 0:
            report_lines.append(f"- Record additional {coverage['missing_steps']} steps to complete coverage")
        if deltas['timing_deltas']:
            report_lines.append("- Review steps with timing issues for efficiency improvements")
        report_lines.append("")

        return '\n'.join(report_lines)


def analyze_instruction_and_video(instruction_json: str, video_path: str, output_dir: str = None) -> Dict:
    """Main function to analyze instructions and video."""
    print("\n=== Starting Analysis ===\n")

    # Set up output directory
    if output_dir:
        output_path = Path(output_dir)
    else:
        output_path = Path(video_path).parent / 'analysis_results'
    output_path.mkdir(exist_ok=True)

    # Analyze instructions
    print("1. Analyzing Instructions...")
    inst_analyzer = InstructionAnalyzer(instruction_json)
    instruction_analysis = inst_analyzer.analyze()

    # Save instruction analysis
    with open(output_path / 'instruction_analysis.json', 'w') as f:
        json.dump(instruction_analysis, f, indent=2, default=str)

    # Generate checklist
    checklist = inst_analyzer.generate_checklist()
    with open(output_path / 'assembly_checklist.md', 'w') as f:
        f.write(checklist)

    print(f"  - Found {instruction_analysis['summary']['total_steps']} assembly steps")
    print(f"  - Found {instruction_analysis['summary']['total_parts']} parts")
    print(f"  - Found {instruction_analysis['summary']['total_tests']} test procedures")

    # Analyze video
    print("\n2. Analyzing Video Recording...")
    video_analyzer = VideoRecordingAnalyzer(video_path)
    motion_events = video_analyzer.detect_motion_events()
    activity_periods = video_analyzer.identify_activity_periods()

    video_analysis = {
        'video_path': str(video_path),
        'duration': video_analyzer.duration,
        'fps': video_analyzer.fps,
        'frame_count': video_analyzer.frame_count,
        'motion_events': motion_events,
        'activity_periods': activity_periods
    }

    # Save video analysis
    with open(output_path / 'video_analysis.json', 'w') as f:
        json.dump(video_analysis, f, indent=2, default=str)

    print(f"  - Duration: {video_analyzer.duration:.1f} seconds")
    print(f"  - Found {len(activity_periods)} activity periods")

    video_analyzer.close()

    # Compare instruction with video
    print("\n3. Comparing Instructions with Video...")
    comparator = InstructionVideoComparator(instruction_analysis, video_analysis)
    comparison_report = comparator.generate_comparison_report()

    # Save comparison report
    with open(output_path / 'comparison_report.md', 'w') as f:
        f.write(comparison_report)

    print(f"\n✅ Analysis complete!")
    print(f"📁 Results saved to: {output_path}")

    return {
        'instruction_analysis': instruction_analysis,
        'video_analysis': video_analysis,
        'output_dir': str(output_path)
    }


def main():
    """Main function for command-line usage."""
    if len(sys.argv) < 3:
        print("Usage: python instruction_analyzer.py <instruction_json> <video_file> [output_dir]")
        sys.exit(1)

    instruction_json = sys.argv[1]
    video_file = sys.argv[2]
    output_dir = sys.argv[3] if len(sys.argv) > 3 else None

    results = analyze_instruction_and_video(instruction_json, video_file, output_dir)

    return results


if __name__ == "__main__":
    main()