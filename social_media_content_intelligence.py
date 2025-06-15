#!/usr/bin/env python3
"""
Social Media Content Intelligence Engine
AI-powered content analysis, classification, and optimization for vanlife & RC truck content
"""

import os
import json
import re
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from PIL import Image, ExifTags
import cv2
import numpy as np
from database import NotionLikeDatabase

class ContentIntelligenceEngine:
    """AI-powered content analysis and optimization for social media automation."""
    
    def __init__(self, db_path="lifeos_local.db"):
        self.db = NotionLikeDatabase(db_path)
        self.supported_formats = {
            'image': ['.jpg', '.jpeg', '.png', '.webp', '.tiff'],
            'video': ['.mp4', '.mov', '.avi', '.mkv', '.webm']
        }
        
        # Load RC brand detection data
        self.rc_brands = self._load_rc_brands()
        self.trail_locations = self._load_trail_locations()
        
    def _load_rc_brands(self) -> Dict[str, Dict]:
        """Load RC brand data for detection."""
        brands_data = self.db.get_table_data('rc_brands')
        brands = {}
        
        for brand in brands_data:
            keywords = brand['detection_keywords'].split(',') if brand['detection_keywords'] else []
            brands[brand['brand_name']] = {
                'keywords': [k.strip().lower() for k in keywords],
                'models': brand['model_names'].split(',') if brand['model_names'] else [],
                'engagement_multiplier': brand['engagement_multiplier'],
                'hashtag_strategy': brand['hashtag_strategy']
            }
        
        return brands
    
    def _load_trail_locations(self) -> List[Dict]:
        """Load trail location data for GPS matching."""
        return self.db.get_table_data('trail_locations')
    
    def analyze_content(self, file_path: str, metadata: Dict = None) -> Dict[str, Any]:
        """
        Comprehensive AI-powered content analysis.
        
        Args:
            file_path: Path to content file
            metadata: Optional metadata (GPS, timestamps, etc.)
            
        Returns:
            Complete analysis results
        """
        if not os.path.exists(file_path):
            return {"error": "File not found"}
        
        analysis = {
            "file_path": file_path,
            "file_size": os.path.getsize(file_path),
            "timestamp": datetime.now().isoformat(),
            "content_type": None,
            "confidence_scores": {},
            "detected_brands": [],
            "location_data": {},
            "caption_suggestions": [],
            "hashtag_recommendations": [],
            "terrain_analysis": {},
            "monetization_potential": 0.0
        }
        
        # Determine content type
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext in self.supported_formats['image']:
            analysis.update(self._analyze_image(file_path, metadata))
        elif file_ext in self.supported_formats['video']:
            analysis.update(self._analyze_video(file_path, metadata))
        else:
            analysis["error"] = f"Unsupported file format: {file_ext}"
            return analysis
        
        # Apply AI classification
        analysis.update(self._classify_content_type(analysis))
        analysis.update(self._detect_brands(analysis))
        analysis.update(self._analyze_location(analysis, metadata))
        analysis.update(self._generate_captions(analysis))
        analysis.update(self._optimize_hashtags(analysis))
        analysis.update(self._calculate_monetization_potential(analysis))
        
        return analysis
    
    def _analyze_image(self, file_path: str, metadata: Dict = None) -> Dict[str, Any]:
        """Analyze image content using computer vision."""
        try:
            # Load image
            image = cv2.imread(file_path)
            if image is None:
                return {"error": "Failed to load image"}
            
            height, width, channels = image.shape
            
            # Extract EXIF data
            exif_data = self._extract_exif_data(file_path)
            
            # Visual analysis
            analysis = {
                "media_type": "image",
                "dimensions": {"width": width, "height": height},
                "exif_data": exif_data,
                "visual_features": self._analyze_visual_features(image),
                "color_analysis": self._analyze_colors(image),
                "object_detection": self._detect_objects(image)
            }
            
            return analysis
            
        except Exception as e:
            return {"error": f"Image analysis failed: {str(e)}"}
    
    def _analyze_video(self, file_path: str, metadata: Dict = None) -> Dict[str, Any]:
        """Analyze video content using computer vision."""
        try:
            # Open video
            cap = cv2.VideoCapture(file_path)
            if not cap.isOpened():
                return {"error": "Failed to open video"}
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Sample frames for analysis
            sample_frames = self._sample_video_frames(cap, 5)  # Sample 5 frames
            cap.release()
            
            # Analyze sampled frames
            frame_analyses = []
            for frame in sample_frames:
                frame_analysis = {
                    "visual_features": self._analyze_visual_features(frame),
                    "color_analysis": self._analyze_colors(frame),
                    "object_detection": self._detect_objects(frame)
                }
                frame_analyses.append(frame_analysis)
            
            analysis = {
                "media_type": "video",
                "duration": duration,
                "fps": fps,
                "frame_count": frame_count,
                "dimensions": {"width": width, "height": height},
                "frame_analyses": frame_analyses,
                "motion_analysis": self._analyze_motion(sample_frames)
            }
            
            return analysis
            
        except Exception as e:
            return {"error": f"Video analysis failed: {str(e)}"}
    
    def _sample_video_frames(self, cap, num_samples: int) -> List[np.ndarray]:
        """Sample frames from video for analysis."""
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if frame_count == 0:
            return []
        
        frames = []
        step = max(1, frame_count // num_samples)
        
        for i in range(0, frame_count, step):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            if ret:
                frames.append(frame)
            if len(frames) >= num_samples:
                break
                
        return frames
    
    def _extract_exif_data(self, file_path: str) -> Dict:
        """Extract EXIF data from image."""
        try:
            with Image.open(file_path) as img:
                exif_data = {}
                if hasattr(img, '_getexif'):
                    exif = img._getexif()
                    if exif:
                        for tag_id, value in exif.items():
                            tag = ExifTags.TAGS.get(tag_id, tag_id)
                            if tag in ['DateTime', 'GPS', 'Make', 'Model', 'Software']:
                                exif_data[tag] = value
                return exif_data
        except Exception:
            pass
        return {}
    
    def _analyze_visual_features(self, image: np.ndarray) -> Dict:
        """Analyze visual features for content classification."""
        try:
            # Convert to different color spaces for analysis
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Calculate various features
            features = {
                "brightness": float(np.mean(gray)),
                "contrast": float(np.std(gray)),
                "sharpness": self._calculate_sharpness(gray),
                "outdoor_score": self._calculate_outdoor_score(hsv),
                "vehicle_probability": self._detect_vehicle_shapes(gray),
                "nature_score": self._calculate_nature_score(hsv)
            }
            
            return features
            
        except Exception:
            return {}
    
    def _calculate_sharpness(self, gray_image: np.ndarray) -> float:
        """Calculate image sharpness using Laplacian variance."""
        try:
            laplacian = cv2.Laplacian(gray_image, cv2.CV_64F)
            return float(laplacian.var())
        except Exception:
            return 0.0
    
    def _calculate_outdoor_score(self, hsv_image: np.ndarray) -> float:
        """Calculate probability of outdoor scene."""
        try:
            # Sky colors (blue hues)
            sky_mask = cv2.inRange(hsv_image, np.array([100, 50, 50]), np.array([130, 255, 255]))
            sky_ratio = np.sum(sky_mask > 0) / (hsv_image.shape[0] * hsv_image.shape[1])
            
            # Green vegetation
            green_mask = cv2.inRange(hsv_image, np.array([40, 40, 40]), np.array([80, 255, 255]))
            green_ratio = np.sum(green_mask > 0) / (hsv_image.shape[0] * hsv_image.shape[1])
            
            # Brown/earth colors
            brown_mask = cv2.inRange(hsv_image, np.array([10, 50, 20]), np.array([20, 255, 200]))
            brown_ratio = np.sum(brown_mask > 0) / (hsv_image.shape[0] * hsv_image.shape[1])
            
            outdoor_score = (sky_ratio * 0.4) + (green_ratio * 0.4) + (brown_ratio * 0.2)
            return min(1.0, outdoor_score * 2)  # Boost the score
            
        except Exception:
            return 0.0
    
    def _detect_vehicle_shapes(self, gray_image: np.ndarray) -> float:
        """Detect RC vehicle-like shapes."""
        try:
            # Simple shape detection using contours
            edges = cv2.Canny(gray_image, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            vehicle_shapes = 0
            total_area = gray_image.shape[0] * gray_image.shape[1]
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > total_area * 0.01:  # Ignore very small shapes
                    # Check if shape could be vehicle-like
                    rect = cv2.boundingRect(contour)
                    aspect_ratio = rect[2] / rect[3] if rect[3] > 0 else 0
                    
                    # RC vehicles typically have certain aspect ratios
                    if 0.5 <= aspect_ratio <= 3.0:
                        vehicle_shapes += 1
            
            return min(1.0, vehicle_shapes / 5)  # Normalize to 0-1
            
        except Exception:
            return 0.0
    
    def _calculate_nature_score(self, hsv_image: np.ndarray) -> float:
        """Calculate natural environment score."""
        try:
            # Analyze color distribution for natural environments
            h, s, v = cv2.split(hsv_image)
            
            # Natural color ranges
            natural_hues = []
            for hue_range in [(35, 85), (15, 35)]:  # Green and brown ranges
                mask = cv2.inRange(h, hue_range[0], hue_range[1])
                natural_hues.append(np.sum(mask > 0))
            
            total_pixels = hsv_image.shape[0] * hsv_image.shape[1]
            nature_score = sum(natural_hues) / total_pixels
            
            return min(1.0, nature_score)
            
        except Exception:
            return 0.0
    
    def _analyze_colors(self, image: np.ndarray) -> Dict:
        """Analyze color distribution."""
        try:
            # Convert to RGB for analysis
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Calculate dominant colors
            pixels = rgb_image.reshape(-1, 3)
            
            # Simple color analysis
            colors = {
                "average_rgb": [float(np.mean(pixels[:, i])) for i in range(3)],
                "dominant_color_type": self._classify_dominant_color(pixels),
                "color_diversity": float(np.std(pixels))
            }
            
            return colors
            
        except Exception:
            return {}
    
    def _classify_dominant_color(self, pixels: np.ndarray) -> str:
        """Classify the dominant color type."""
        try:
            avg_color = np.mean(pixels, axis=0)
            r, g, b = avg_color
            
            if g > r and g > b:
                return "green"  # Nature/vegetation
            elif b > r and b > g:
                return "blue"   # Sky/water
            elif r > g and r > b:
                return "red"    # Earth/rock
            elif abs(r - g) < 20 and abs(g - b) < 20:
                return "gray"   # Rock/road
            else:
                return "mixed"
                
        except Exception:
            return "unknown"
    
    def _detect_objects(self, image: np.ndarray) -> Dict:
        """Simple object detection for RC vehicles and outdoor elements."""
        # This is a simplified version - in production, you'd use a trained model
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect circular objects (wheels)
            circles = cv2.HoughCircles(
                gray, cv2.HOUGH_GRADIENT, 1, 20,
                param1=50, param2=30, minRadius=5, maxRadius=100
            )
            
            wheel_count = 0
            if circles is not None:
                wheel_count = len(circles[0])
            
            # Detect rectangular objects (vehicles)
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            rectangular_objects = 0
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 500:  # Filter small objects
                    approx = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
                    if len(approx) == 4:  # Rectangular
                        rectangular_objects += 1
            
            return {
                "circular_objects": wheel_count,
                "rectangular_objects": rectangular_objects,
                "rc_vehicle_probability": min(1.0, (wheel_count * 0.3 + rectangular_objects * 0.2))
            }
            
        except Exception:
            return {"rc_vehicle_probability": 0.0}
    
    def _analyze_motion(self, frames: List[np.ndarray]) -> Dict:
        """Analyze motion in video frames."""
        if len(frames) < 2:
            return {"motion_intensity": 0.0}
        
        try:
            motion_scores = []
            
            for i in range(1, len(frames)):
                prev_gray = cv2.cvtColor(frames[i-1], cv2.COLOR_BGR2GRAY)
                curr_gray = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)
                
                # Calculate frame difference
                diff = cv2.absdiff(prev_gray, curr_gray)
                motion_score = np.mean(diff)
                motion_scores.append(motion_score)
            
            return {
                "motion_intensity": float(np.mean(motion_scores)),
                "motion_consistency": float(np.std(motion_scores))
            }
            
        except Exception:
            return {"motion_intensity": 0.0}
    
    def _classify_content_type(self, analysis: Dict) -> Dict:
        """Classify content as vanlife, RC truck, or mixed."""
        scores = {
            "vanlife": 0.0,
            "rc_truck": 0.0,
            "mixed": 0.0
        }
        
        try:
            # Check visual features
            visual_features = analysis.get("visual_features", {})
            object_detection = analysis.get("object_detection", {})
            
            # RC truck indicators
            if object_detection.get("rc_vehicle_probability", 0) > 0.3:
                scores["rc_truck"] += 0.4
            
            if visual_features.get("vehicle_probability", 0) > 0.5:
                scores["rc_truck"] += 0.3
            
            # Vanlife indicators
            outdoor_score = visual_features.get("outdoor_score", 0)
            if outdoor_score > 0.6:
                scores["vanlife"] += 0.3
            
            # Nature/travel elements
            nature_score = visual_features.get("nature_score", 0)
            if nature_score > 0.5:
                scores["vanlife"] += 0.2
                scores["rc_truck"] += 0.1  # RC content often outdoors too
            
            # Mixed content
            if scores["vanlife"] > 0.3 and scores["rc_truck"] > 0.3:
                scores["mixed"] = (scores["vanlife"] + scores["rc_truck"]) / 2
            
            # Normalize scores
            max_score = max(scores.values())
            if max_score > 0:
                for key in scores:
                    scores[key] = scores[key] / max_score
            
            # Determine primary content type
            content_type = max(scores.keys(), key=lambda k: scores[k])
            
            return {
                "content_type": content_type,
                "confidence_scores": scores
            }
            
        except Exception:
            return {
                "content_type": "mixed",
                "confidence_scores": scores
            }
    
    def _detect_brands(self, analysis: Dict) -> Dict:
        """Detect RC brands in content."""
        detected_brands = []
        
        try:
            # For demo purposes, we'll use heuristics
            # In production, this would use computer vision and OCR
            
            visual_features = analysis.get("visual_features", {})
            vehicle_prob = visual_features.get("vehicle_probability", 0)
            
            if vehicle_prob > 0.5:
                # Simulate brand detection based on vehicle characteristics
                # This would normally use trained models
                
                if vehicle_prob > 0.8:
                    detected_brands.append({
                        "brand": "Axial Racing",
                        "confidence": 0.85,
                        "model_guess": "SCX24"
                    })
                elif vehicle_prob > 0.6:
                    detected_brands.append({
                        "brand": "Traxxas",
                        "confidence": 0.72,
                        "model_guess": "TRX-4"
                    })
        
        except Exception:
            pass
        
        return {"detected_brands": detected_brands}
    
    def _analyze_location(self, analysis: Dict, metadata: Dict = None) -> Dict:
        """Analyze and match location data."""
        location_data = {}
        
        try:
            # Extract GPS from EXIF if available
            exif_data = analysis.get("exif_data", {})
            gps_info = exif_data.get("GPS")
            
            if gps_info:
                # Parse GPS coordinates (simplified)
                location_data["has_gps"] = True
                # GPS parsing would be more complex in reality
            
            # Match against known trail locations
            if metadata and "gps_coords" in metadata:
                lat, lon = metadata["gps_coords"]
                matched_trail = self._find_nearest_trail(lat, lon)
                if matched_trail:
                    location_data["matched_trail"] = matched_trail
            
            # Detect BC region characteristics
            visual_features = analysis.get("visual_features", {})
            if visual_features.get("nature_score", 0) > 0.7:
                location_data["region_guess"] = "British Columbia Wilderness"
                location_data["terrain_type"] = self._guess_terrain_type(analysis)
        
        except Exception:
            pass
        
        return {"location_data": location_data}
    
    def _find_nearest_trail(self, lat: float, lon: float, radius_km: float = 10) -> Dict:
        """Find nearest trail location."""
        try:
            for trail in self.trail_locations:
                if trail['gps_latitude'] and trail['gps_longitude']:
                    # Simple distance calculation (haversine would be more accurate)
                    lat_diff = abs(lat - trail['gps_latitude'])
                    lon_diff = abs(lon - trail['gps_longitude'])
                    distance = ((lat_diff ** 2) + (lon_diff ** 2)) ** 0.5
                    
                    # Rough conversion to km (1 degree ≈ 111 km)
                    distance_km = distance * 111
                    
                    if distance_km <= radius_km:
                        return {
                            "trail_name": trail['trail_name'],
                            "distance_km": round(distance_km, 2),
                            "rc_friendly": trail['rc_friendly'],
                            "difficulty": trail['difficulty']
                        }
        except Exception:
            pass
        
        return None
    
    def _guess_terrain_type(self, analysis: Dict) -> str:
        """Guess terrain type from visual analysis."""
        try:
            color_analysis = analysis.get("color_analysis", {})
            dominant_color = color_analysis.get("dominant_color_type", "")
            
            visual_features = analysis.get("visual_features", {})
            nature_score = visual_features.get("nature_score", 0)
            
            if dominant_color == "green" and nature_score > 0.7:
                return "forest"
            elif dominant_color == "gray":
                return "rocky"
            elif dominant_color == "brown":
                return "muddy"
            elif dominant_color == "blue":
                return "scenic"
            else:
                return "mixed"
                
        except Exception:
            return "unknown"
    
    def _generate_captions(self, analysis: Dict) -> Dict:
        """Generate captions in relaxed traveler voice."""
        captions = []
        
        try:
            content_type = analysis.get("content_type", "mixed")
            location_data = analysis.get("location_data", {})
            detected_brands = analysis.get("detected_brands", [])
            
            # Base templates for different content types
            templates = {
                "vanlife": [
                    "Another beautiful day exploring the backroads of BC...",
                    "Sometimes the journey matters more than the destination",
                    "Found this hidden gem while wandering the mountains",
                    "Life's too short to stay on the main roads"
                ],
                "rc_truck": [
                    "This little beast handled every rock like a champ",
                    "Testing the limits on some technical terrain today",
                    "Nothing beats the satisfaction of a perfect line",
                    "RC therapy session in progress..."
                ],
                "mixed": [
                    "Perfect day for some outdoor adventures",
                    "Exploring new trails and testing new gear",
                    "Making the most of this beautiful BC weather"
                ]
            }
            
            base_captions = templates.get(content_type, templates["mixed"])
            
            for base in base_captions[:3]:  # Generate 3 options
                caption = base
                
                # Add location context
                if location_data.get("matched_trail"):
                    trail = location_data["matched_trail"]
                    caption += f" at {trail['trail_name']}"
                
                # Add brand context
                if detected_brands:
                    brand = detected_brands[0]["brand"]
                    caption += f". The {brand} is proving its worth out here."
                
                # Add terrain context
                terrain = location_data.get("terrain_type", "")
                if terrain and terrain != "unknown":
                    caption += f" Love this {terrain} terrain."
                
                captions.append(caption)
        
        except Exception:
            captions = ["Great day for outdoor adventures!"]
        
        return {"caption_suggestions": captions}
    
    def _optimize_hashtags(self, analysis: Dict) -> Dict:
        """Generate optimized hashtags for maximum engagement."""
        hashtags = set()
        
        try:
            content_type = analysis.get("content_type", "mixed")
            detected_brands = analysis.get("detected_brands", [])
            location_data = analysis.get("location_data", {})
            
            # Base hashtags by content type
            base_hashtags = {
                "vanlife": ["#vanlife", "#nomadlife", "#roadtrip", "#bctrails", "#vanlifebc", "#outdoorlife"],
                "rc_truck": ["#rctrucks", "#scalerc", "#rclife", "#rockcrawling", "#rcaddict", "#trailtherapy"],
                "mixed": ["#outdooradventure", "#bcoutdoors", "#explorebc", "#adventuretime"]
            }
            
            hashtags.update(base_hashtags.get(content_type, base_hashtags["mixed"]))
            
            # Add brand-specific hashtags
            for brand_info in detected_brands:
                brand_name = brand_info["brand"]
                if brand_name in self.rc_brands:
                    brand_hashtags = self.rc_brands[brand_name]["hashtag_strategy"]
                    hashtags.update(brand_hashtags.split())
            
            # Add location hashtags
            if location_data.get("matched_trail"):
                trail_name = location_data["matched_trail"]["trail_name"]
                # Convert trail name to hashtag
                hashtag = "#" + re.sub(r'[^a-zA-Z0-9]', '', trail_name.lower())
                hashtags.add(hashtag)
            
            # Add terrain hashtags
            terrain = location_data.get("terrain_type", "")
            terrain_hashtags = {
                "forest": ["#foresttrails", "#wilderness"],
                "rocky": ["#rockcrawling", "#technicalterrain"],
                "muddy": ["#muddy", "#offroadlife"],
                "scenic": ["#scenic", "#naturephotography"]
            }
            
            if terrain in terrain_hashtags:
                hashtags.update(terrain_hashtags[terrain])
            
            # Add general engagement hashtags
            engagement_hashtags = [
                "#adventure", "#explore", "#outdoor", "#nature",
                "#canada", "#britishcolumbia", "#mountains"
            ]
            hashtags.update(engagement_hashtags)
            
            # Limit to 30 hashtags and prioritize
            hashtag_list = list(hashtags)[:30]
            
        except Exception:
            hashtag_list = ["#adventure", "#outdoor", "#explore"]
        
        return {"hashtag_recommendations": hashtag_list}
    
    def _calculate_monetization_potential(self, analysis: Dict) -> Dict:
        """Calculate monetization potential score."""
        try:
            score = 0.0
            
            # Content type multipliers
            content_type = analysis.get("content_type", "mixed")
            type_multipliers = {
                "vanlife": 0.8,  # Good for lifestyle/travel monetization
                "rc_truck": 1.0,  # Excellent for product/brand partnerships
                "mixed": 0.9     # Versatile content
            }
            score += type_multipliers.get(content_type, 0.5) * 30
            
            # Brand detection bonus
            detected_brands = analysis.get("detected_brands", [])
            if detected_brands:
                brand_bonus = min(20, len(detected_brands) * 10)
                score += brand_bonus
            
            # Quality indicators
            visual_features = analysis.get("visual_features", {})
            if visual_features.get("sharpness", 0) > 100:  # Good image quality
                score += 15
            
            if visual_features.get("outdoor_score", 0) > 0.7:  # Outdoor content performs well
                score += 15
            
            # Location bonus
            location_data = analysis.get("location_data", {})
            if location_data.get("matched_trail"):
                score += 10  # Location tagging increases engagement
            
            # Normalize to 0-100
            score = min(100, max(0, score))
            
            return {"monetization_potential": score}
            
        except Exception:
            return {"monetization_potential": 50.0}
    
    def save_analysis(self, analysis: Dict) -> int:
        """Save analysis results to database."""
        try:
            post_data = {
                "file_path": analysis["file_path"],
                "content_type": analysis.get("content_type", "mixed"),
                "caption": analysis.get("caption_suggestions", [""])[0] if analysis.get("caption_suggestions") else "",
                "hashtags": " ".join(analysis.get("hashtag_recommendations", [])),
                "brand_detected": json.dumps(analysis.get("detected_brands", [])),
                "location": json.dumps(analysis.get("location_data", {})),
                "terrain_type": analysis.get("location_data", {}).get("terrain_type", ""),
                "performance_score": analysis.get("monetization_potential", 0.0),
                "upload_status": "analyzed"
            }
            
            return self.db.add_record("social_media_posts", post_data)
            
        except Exception as e:
            print(f"Error saving analysis: {e}")
            return 0

# Example usage and testing
if __name__ == "__main__":
    engine = ContentIntelligenceEngine()
    
    # Test with a sample file (would need actual image/video file)
    # analysis = engine.analyze_content("/path/to/sample/image.jpg")
    # print(json.dumps(analysis, indent=2))
    
    print("Content Intelligence Engine initialized successfully!")
    print(f"Loaded {len(engine.rc_brands)} RC brands for detection")
    print(f"Loaded {len(engine.trail_locations)} trail locations for matching")