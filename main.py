#!/usr/bin/env python3
import argparse
import json
import os
import csv
import glob
from pathlib import Path
from omr.processor import OMRProcessor

def main():
    parser = argparse.ArgumentParser(description="NAPOLCOM OMR Parser")
    
    # Set layout mode
    parser.add_argument("--set-layout", action="store_true", 
                      help="Run the template creation wizard")
    
    # Input files
    parser.add_argument("input", nargs="*", 
                      help="Input image files (supports glob patterns)")
    
    # Output options
    parser.add_argument("--out", type=str, default="results.csv",
                      help="Output file path (CSV or JSON)")
    
    # Template
    parser.add_argument("--template", type=str, default="template.json",
                      help="Template JSON file")
    
    # Grading
    parser.add_argument("--grade", action="store_true",
                      help="Grade sheets if answer keys are available")
    
    args = parser.parse_args()
    
    # Create processor
    processor = OMRProcessor(args.template if not args.set_layout else None)
    
    # Handle template creation mode
    if args.set_layout:
        if len(args.input) < 1 or len(args.input) > 2:
            print("Error: --set-layout requires 1-2 arguments: <blank_sheet> [output_template]")
            return 1
            
        blank_sheet = args.input[0]
        template_output = args.input[1] if len(args.input) == 2 else args.template
        
        processor.generate_template(blank_sheet, template_output)
        print(f"Template created and saved to {template_output}")
        return 0
    
    # Process sheets
    if not args.input:
        print("Error: No input files specified")
        return 1
    
    # Expand any glob patterns
    input_files = []
    for pattern in args.input:
        input_files.extend(glob.glob(pattern))
    
    if not input_files:
        print("Error: No files found matching the patterns")
        return 1
    
    results = []
    
    for file_path in input_files:
        print(f"Processing {file_path}...")
        try:
            with open(file_path, 'rb') as f:
                img_data = f.read()
                
            result = processor.process_sheet(img_data)
            
            # Add filename to result for reference
            result["filename"] = os.path.basename(file_path)
            
            # Grade if requested
            if args.grade:
                set_type = result.get("set_type", "Unknown")
                if set_type in ["A", "B", "C"]:
                    answer_key_path = f"keys/napolcom_2025_set{set_type}.json"
                    if os.path.exists(answer_key_path):
                        score = processor.grade(result["answers"], answer_key_path)
                        result["raw_score"] = score
                    else:
                        print(f"Warning: Answer key not found: {answer_key_path}")
                        result["raw_score"] = None
                else:
                    print(f"Warning: Unknown set type '{set_type}' for {file_path}")
                    result["raw_score"] = None
            
            results.append(result)
            print(f"  Processed successfully")
            
        except Exception as e:
            print(f"  Error processing {file_path}: {e}")
    
    # Save results
    output_path = args.out
    output_ext = os.path.splitext(output_path)[1].lower()
    
    if output_ext == ".json":
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
    else:  # Default to CSV
        if results:
            # Get all possible field names across all results
            fieldnames = set()
            for result in results:
                fieldnames.update(result.keys())
                if "answers" in result:
                    for q in result["answers"]:
                        fieldnames.add(f"q{q}")
            
            # Sort fieldnames to get consistent output
            fieldnames = sorted(fieldnames)
            
            # Remove 'answers' field since we'll flatten it
            if "answers" in fieldnames:
                fieldnames.remove("answers")
            
            with open(output_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for result in results:
                    # Flatten answers into q1, q2, etc.
                    row = {k: v for k, v in result.items() if k != "answers"}
                    if "answers" in result:
                        for q, ans in result["answers"].items():
                            row[f"q{q}"] = ans
                    
                    writer.writerow(row)
    
    print(f"Results saved to {output_path}")
    print(f"Processed {len(results)} of {len(input_files)} files successfully")
    
    return 0

if __name__ == "__main__":
    exit(main())
