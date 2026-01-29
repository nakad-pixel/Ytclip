#!/usr/bin/env python3
"""
Earning Calculator: Calculate earning potential for viral clips
Analyzes virality, engagement, and CPM rates to estimate revenue potential.
"""

import logging
from typing import Dict, Any, List, Optional
import math

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EarningCalculator:
    """Calculate earning potential for video clips based on multiple factors."""

    # CPM rates by niche (cost per 1000 views in USD)
    NICHE_CPM_RATES = {
        'fortnite': {'min': 8.0, 'max': 15.0, 'avg': 11.5},
        'horror': {'min': 4.0, 'max': 8.0, 'avg': 6.0},
        'roblox': {'min': 2.0, 'max': 4.0, 'avg': 3.0},
        'minecraft': {'min': 3.0, 'max': 7.0, 'avg': 5.0},
        'call_of_duty': {'min': 7.0, 'max': 12.0, 'avg': 9.5},
        'valorant': {'min': 6.0, 'max': 11.0, 'avg': 8.5},
        'gaming': {'min': 3.0, 'max': 8.0, 'avg': 5.5},  # Default for unknown niches
    }

    # Base view counts by niche (estimated average views for viral content)
    NICHE_BASE_VIEWS = {
        'fortnite': 150000,    # High engagement
        'horror': 100000,      # Medium-high engagement
        'roblox': 80000,       # Medium engagement
        'minecraft': 120000,    # High engagement
        'call_of_duty': 140000, # High engagement
        'valorant': 110000,     # High engagement
        'gaming': 90000,        # Default
    }

    # Brand safety penalty multipliers
    SAFETY_PENALTIES = {
        'profanity': -0.30,        # 30% reduction for excessive profanity
        'violence': -0.20,        # 20% reduction for violence
        'controversy': -0.25,     # 25% reduction for controversial content
        'copyright': -0.35,       # 35% reduction for copyright concerns
        'explicit': -0.40,         # 40% reduction for explicit content
    }

    def __init__(self):
        """Initialize earning calculator."""
        logger.info("Initialized EarningCalculator")

    def calculate_earning_potential(self, clip_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate earning potential for a clip.

        Args:
            clip_data: Dictionary containing clip information:
                - virality_score: Virality score from 0-100
                - niche: Gaming niche (fortnite, horror, roblox, etc.)
                - engagement_metrics: Dict with engagement data from Gemini
                - brand_safety: Dict with safety flags
                - moment_type: Type of viral moment

        Returns:
            Dictionary with earning potential analysis
        """
        if not clip_data:
            return self._empty_result("No clip data provided")

        # Extract data
        virality_score = clip_data.get('virality_score', 0)
        niche = self._normalize_niche(clip_data.get('niche', 'gaming'))
        engagement_metrics = clip_data.get('engagement_metrics', {})
        brand_safety = clip_data.get('brand_safety', {})
        moment_type = clip_data.get('moment_type', '')

        # Calculate base CPM
        cpm_info = self._get_cpm_for_niche(niche)
        base_cpm = cpm_info['avg']

        # Calculate expected views based on virality
        expected_views = self._calculate_expected_views(virality_score, niche)

        # Calculate engagement quality score
        engagement_score = self._calculate_engagement_score(engagement_metrics)

        # Calculate brand safety score
        safety_score = self._calculate_safety_score(brand_safety)

        # Calculate base earning potential score (0-100)
        base_earning_score = self._calculate_base_score(
            virality_score, engagement_score, base_cpm
        )

        # Apply brand safety penalties
        final_earning_score = self._apply_safety_penalties(base_earning_score, brand_safety)

        # Calculate revenue estimation
        estimated_revenue = self._calculate_revenue(
            expected_views, base_cpm, safety_score
        )

        # Compile results
        result = {
            'clip_id': clip_data.get('clip_id', 'unknown'),
            'niche': niche,
            'virality_score': virality_score,
            'expected_views': expected_views,
            'engagement_score': engagement_score,
            'safety_score': safety_score,
            'base_cpm': base_cpm,
            'cpm_range': f"${cpm_info['min']:.1f} - ${cpm_info['max']:.1f}",
            'base_earning_score': base_earning_score,
            'final_earning_score': final_earning_score,
            'estimated_revenue': estimated_revenue,
            'revenue_range': self._calculate_revenue_range(expected_views, cpm_info),
            'moment_type': moment_type,
            'safety_flags': self._get_safety_flags(brand_safety),
            'ranking_factors': {
                'virality_weight': 0.4,
                'engagement_weight': 0.3,
                'cpm_weight': 0.2,
                'safety_weight': 0.1
            }
        }

        logger.debug(f"Calculated earning potential for clip {result['clip_id']}: "
                    f"Score {final_earning_score:.1f}/100, Revenue ${estimated_revenue:.2f}")

        return result

    def _normalize_niche(self, niche: str) -> str:
        """Normalize niche name to standard format."""
        niche = niche.lower().strip()
        
        # Map common variations
        niche_map = {
            'fortnite': 'fortnite',
            'minecraft': 'minecraft',
            'roblox': 'roblox',
            'horror': 'horror',
            'call_of_duty': 'call_of_duty',
            'cod': 'call_of_duty',
            'valorant': 'valorant',
            'apex': 'gaming',
            'pubg': 'gaming',
            'gta': 'gaming'
        }
        
        return niche_map.get(niche, 'gaming')

    def _get_cpm_for_niche(self, niche: str) -> Dict[str, float]:
        """Get CPM rates for a niche."""
        return self.NICHE_CPM_RATES.get(niche, self.NICHE_CPM_RATES['gaming'])

    def _calculate_expected_views(self, virality_score: float, niche: str) -> int:
        """Calculate expected views based on virality score and niche."""
        base_views = self.NICHE_BASE_VIEWS.get(niche, 90000)
        
        # Exponential scaling based on virality
        # Score 0 = 0 views, Score 100 = 3x base views
        multiplier = (virality_score / 100) ** 1.2 * 3
        expected_views = int(base_views * multiplier)
        
        # Ensure minimum and maximum bounds
        expected_views = max(1000, min(expected_views, 1000000))
        
        return expected_views

    def _calculate_engagement_score(self, engagement_metrics: Dict[str, Any]) -> float:
        """Calculate engagement quality score from Gemini metrics."""
        if not engagement_metrics:
            return 50.0  # Neutral score if no data

        # Extract key engagement indicators
        excitement_level = engagement_metrics.get('excitement_level', 50)
        emotional_arc = engagement_metrics.get('emotional_arc', 50)
        hook_strength = engagement_metrics.get('hook_strength', 50)
        
        # Calculate weighted average
        engagement_score = (
            excitement_level * 0.4 +
            emotional_arc * 0.35 +
            hook_strength * 0.25
        )
        
        return max(0, min(100, engagement_score))

    def _calculate_safety_score(self, brand_safety: Dict[str, Any]) -> float:
        """Calculate brand safety score."""
        if not brand_safety:
            return 100.0  # Perfect safety if no data

        # Start with perfect score
        safety_score = 100.0
        
        # Apply penalties for safety issues
        for issue, severity in brand_safety.items():
            if severity:  # If issue is flagged
                penalty = self.SAFETY_PENALTIES.get(issue, -0.10)
                safety_score *= (1 + penalty)  # Apply as percentage reduction
        
        return max(0, min(100, safety_score))

    def _calculate_base_score(self, virality_score: float, engagement_score: float, cpm: float) -> float:
        """Calculate base earning potential score."""
        # Normalize CPM to 0-100 scale (assuming max CPM of $20)
        cpm_score = min(100, (cpm / 20.0) * 100)
        
        # Weighted combination
        base_score = (
            virality_score * 0.4 +
            engagement_score * 0.3 +
            cpm_score * 0.2 +
            50 * 0.1  # Default component
        )
        
        return max(0, min(100, base_score))

    def _apply_safety_penalties(self, base_score: float, brand_safety: Dict[str, Any]) -> float:
        """Apply brand safety penalties to earning score."""
        if not brand_safety:
            return base_score
        
        final_score = base_score
        
        for issue, severity in brand_safety.items():
            if severity:  # If issue is flagged
                penalty = self.SAFETY_PENALTIES.get(issue, -0.10)
                final_score *= (1 + penalty)  # Apply as percentage reduction
        
        return max(0, min(100, final_score))

    def _calculate_revenue(self, expected_views: int, cpm: float, safety_score: float) -> float:
        """Calculate estimated revenue."""
        # Base revenue calculation
        base_revenue = (expected_views / 1000) * cpm
        
        # Apply safety score as percentage
        safety_multiplier = safety_score / 100.0
        
        estimated_revenue = base_revenue * safety_multiplier
        
        return round(estimated_revenue, 2)

    def _calculate_revenue_range(self, expected_views: int, cpm_info: Dict[str, float]) -> str:
        """Calculate revenue range (min-max estimate)."""
        min_revenue = self._calculate_revenue(expected_views, cpm_info['min'], 0.7)
        max_revenue = self._calculate_revenue(expected_views, cpm_info['max'], 1.0)
        
        return f"${min_revenue:.2f} - ${max_revenue:.2f}"

    def _get_safety_flags(self, brand_safety: Dict[str, Any]) -> List[str]:
        """Get list of safety flags that were triggered."""
        if not brand_safety:
            return []
        
        return [issue for issue, severity in brand_safety.items() if severity]

    def _empty_result(self, reason: str) -> Dict[str, Any]:
        """Return empty result for invalid input."""
        return {
            'error': reason,
            'final_earning_score': 0,
            'estimated_revenue': 0.0,
            'safety_flags': [],
            'expected_views': 0
        }

    def rank_clips_by_earning_potential(self, clips: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rank multiple clips by earning potential.

        Args:
            clips: List of clip data dictionaries

        Returns:
            List of clips with earning analysis, sorted by earning potential
        """
        scored_clips = []
        
        for clip in clips:
            earning_analysis = self.calculate_earning_potential(clip)
            earning_analysis['clip_data'] = clip  # Keep original data
            scored_clips.append(earning_analysis)
        
        # Sort by final earning score (descending)
        scored_clips.sort(key=lambda x: x['final_earning_score'], reverse=True)
        
        logger.info(f"Ranked {len(scored_clips)} clips by earning potential")
        
        return scored_clips

    def filter_clips_by_criteria(self, clips: List[Dict[str, Any]], 
                                min_virality: float = 70.0,
                                min_safety_score: float = 70.0,
                                exclude_published: bool = True) -> List[Dict[str, Any]]:
        """
        Filter clips based on quality and safety criteria.

        Args:
            clips: List of clip data dictionaries
            min_virality: Minimum virality score required
            min_safety_score: Minimum safety score required
            exclude_published: Whether to exclude already published clips

        Returns:
            Filtered list of clips
        """
        filtered = []
        
        for clip in clips:
            # Calculate earning potential
            earning_analysis = self.calculate_earning_potential(clip)
            
            # Apply filters
            if earning_analysis['virality_score'] < min_virality:
                continue
            
            if earning_analysis['safety_score'] < min_safety_score:
                continue
            
            if exclude_published and self._is_already_published(clip):
                continue
            
            filtered.append(clip)
        
        logger.info(f"Filtered {len(clips)} clips down to {len(filtered)} clips")
        return filtered

    def _is_already_published(self, clip: Dict[str, Any]) -> bool:
        """Check if clip is already published (placeholder - implement with state tracking)."""
        # TODO: Implement state tracking
        return False

    def get_niche_statistics(self) -> Dict[str, Any]:
        """Get CPM and view statistics by niche."""
        return {
            'cpm_rates': self.NICHE_CPM_RATES,
            'base_views': self.NICHE_BASE_VIEWS,
            'safety_penalties': self.SAFETY_PENALTIES
        }