"""
Test script for the OMR processor
"""
import os
import cv2
import matplotlib.pyplot as plt
from src.omr_processor import OMRProcessor
from src.utils.image_utils import load_image, resize_image


def display_image(image, title):
    """Display an image using matplotlib"""
    plt.figure(figsize=(10, 8))
    plt.title(title)
    
    # Convert BGR to RGB for matplotlib
    if len(image.shape) == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    plt.imshow(image, cmap='gray' if len(image.shape) == 2 else None)
    plt.axis('off')
    plt.show()


def test_process_image(image_path, save_results=True):
    """Test processing a single image"""
    print(f"Testing OMR processor with image: {image_path}")
    
    # Create and run the processor in debug mode
    processor = OMRProcessor(debug_mode=True)
    results = processor.process_image(image_path)
    
    # Display the original and aligned images
    display_image(results["original_image"], "Original Image")
    display_image(results["aligned_image"], "Aligned Image")
    
    # Display some of the extracted regions
    personal_info = results["personal_info"]
    
    # Display booklet number region
    if "booklet_number" in personal_info:
        display_image(personal_info["booklet_number"]["roi"], "Booklet Number Region")
        display_image(personal_info["booklet_number"]["cleaned_roi"], "Booklet Number (Grid Removed)")
    
    # Display set type region
    if "set_type" in results:
        display_image(results["set_type"]["roi"], "Set Type Region")
    
    # Display application number region
    if "application_number" in results:
        display_image(results["application_number"]["roi"], "Application Number Region")
    
    # Print a summary of the results
    print("\nProcessing complete. Summary of results:")
    print(f"Set Type: {results['extracted_data']['set_type']}")
    print(f"Application Number: {results['extracted_data']['application_number']}")
    print(f"Number of answers detected: {len(results['extracted_data']['answers'])}")
    
    # Save debug images
    if save_results:
        debug_dir = "test_results/debug"
        os.makedirs(debug_dir, exist_ok=True)
        processor.save_debug_images(debug_dir)
        
        # Save results
        output_path = "test_results/results.json"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        processor.save_results(output_path)
        print(f"\nDebug images saved to: {debug_dir}")
        print(f"Results saved to: {output_path}")


def main():
    # Create output directory
    os.makedirs("test_results", exist_ok=True)
    
    # Path to the test image
    # This should be replaced with an actual path to an OMR form image
    image_path = "data/sample_form.jpg"
    
    # Check if the image exists
    if not os.path.exists(image_path):
        print(f"Warning: Image not found at {image_path}")
        print("Please provide a valid path to an OMR form image.")
        
        # Use the first image found in the data directory as a fallback
        data_dir = "data"
        if os.path.exists(data_dir):
            for file in os.listdir(data_dir):
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.tif', '.bmp')):
                    image_path = os.path.join(data_dir, file)
                    print(f"Using image: {image_path}")
                    break
    
    # Test the processor
    if os.path.exists(image_path):
        test_process_image(image_path)
    else:
        print("No valid image file found to test. Please place an image in the data directory.")


if __name__ == "__main__":
    main()
