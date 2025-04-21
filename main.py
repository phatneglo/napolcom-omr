"""
Main script for running the OMR form processor
"""
import os
import argparse
from src.omr_processor import OMRProcessor


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Process OMR forms.')
    parser.add_argument('image_path', help='Path to the input image')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--output', default='results', help='Output directory')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)
    
    # Create and run the OMR processor
    processor = OMRProcessor(debug_mode=args.debug)
    results = processor.process_image(args.image_path)
    
    # Save results
    output_path = os.path.join(args.output, 'results.json')
    processor.save_results(output_path)
    
    # Save debug images if in debug mode
    if args.debug:
        debug_dir = os.path.join(args.output, 'debug')
        processor.save_debug_images(debug_dir)
    
    # Print a summary of the results
    print("\nProcessing complete. Summary of results:")
    print(f"Set Type: {results['extracted_data']['set_type']}")
    print(f"Application Number: {results['extracted_data']['application_number']}")
    print(f"Number of answers detected: {len(results['extracted_data']['answers'])}")
    
    print(f"\nDetailed results saved to: {output_path}")


if __name__ == "__main__":
    main()
