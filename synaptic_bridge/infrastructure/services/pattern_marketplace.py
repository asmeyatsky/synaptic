"""
CLE Pattern Marketplace

Following PRD Phase 4: Public CLE pattern marketplace for org-to-org pattern sharing.
Allows exporting/importing correction patterns between organizations.
"""

import hashlib
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class PatternListing:
    """A publicly listed CLE pattern."""

    listing_id: str
    pattern_id: str
    owner_org: str
    name: str
    description: str
    from_tool: str
    to_tool: str
    success_rate: float
    usage_count: int
    rating: float
    tags: list[str]
    created_at: str
    price: float = 0.0


@dataclass
class PatternReview:
    """Review of a marketplace pattern."""

    review_id: str
    listing_id: str
    reviewer_org: str
    rating: int
    comment: str
    created_at: str


class CLEPatternMarketplace:
    """
    CLE Pattern Marketplace for sharing correction patterns between organizations.

    Following PRD Phase 4: Public CLE pattern marketplace.
    """

    def __init__(self):
        self._listings: dict[str, PatternListing] = {}
        self._reviews: dict[str, list[PatternReview]] = {}
        self._purchases: dict[str, set[str]] = {}

    def create_listing(
        self,
        org_id: str,
        pattern_id: str,
        name: str,
        description: str,
        from_tool: str,
        to_tool: str,
        success_rate: float,
        tags: list[str],
        price: float = 0.0,
    ) -> PatternListing:
        """Create a new pattern listing."""
        listing_id = f"listing_{uuid.uuid4().hex[:12]}"

        listing = PatternListing(
            listing_id=listing_id,
            pattern_id=pattern_id,
            owner_org=org_id,
            name=name,
            description=description,
            from_tool=from_tool,
            to_tool=to_tool,
            success_rate=success_rate,
            usage_count=0,
            rating=0.0,
            tags=tags,
            price=price,
            created_at=datetime.now(UTC).isoformat(),
        )

        self._listings[listing_id] = listing
        self._reviews[listing_id] = []

        return listing

    def get_listing(self, listing_id: str) -> PatternListing | None:
        """Get a listing by ID."""
        return self._listings.get(listing_id)

    def search_listings(
        self,
        query: str | None = None,
        from_tool: str | None = None,
        to_tool: str | None = None,
        tags: list[str] | None = None,
        max_price: float | None = None,
        min_rating: float | None = None,
    ) -> list[PatternListing]:
        """Search marketplace listings."""
        results = list(self._listings.values())

        if query:
            query_lower = query.lower()
            results = [
                r
                for r in results
                if query_lower in r.name.lower() or query_lower in r.description.lower()
            ]

        if from_tool:
            results = [r for r in results if r.from_tool == from_tool]

        if to_tool:
            results = [r for r in results if r.to_tool == to_tool]

        if tags:
            results = [r for r in results if any(t in r.tags for t in tags)]

        if max_price is not None:
            results = [r for r in results if r.price <= max_price]

        if min_rating is not None:
            results = [r for r in results if r.rating >= min_rating]

        return sorted(results, key=lambda x: x.rating, reverse=True)

    def purchase_listing(self, listing_id: str, org_id: str) -> dict:
        """Purchase/download a pattern listing."""
        listing = self._listings.get(listing_id)
        if not listing:
            raise ValueError("Listing not found")

        if org_id not in self._purchases:
            self._purchases[org_id] = set()

        if listing_id in self._purchases[org_id]:
            return {"status": "already_owned", "listing_id": listing_id}

        if listing.price > 0:
            return {"status": "payment_required", "price": listing.price}

        self._purchases[org_id].add(listing_id)
        listing.usage_count += 1

        return {
            "status": "success",
            "listing_id": listing_id,
            "pattern_id": listing.pattern_id,
        }

    def add_review(
        self,
        listing_id: str,
        reviewer_org: str,
        rating: int,
        comment: str,
    ) -> PatternReview:
        """Add a review to a listing."""
        if listing_id not in self._listings:
            raise ValueError("Listing not found")

        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5")

        review = PatternReview(
            review_id=f"review_{uuid.uuid4().hex[:8]}",
            listing_id=listing_id,
            reviewer_org=reviewer_org,
            rating=rating,
            comment=comment,
            created_at=datetime.now(UTC).isoformat(),
        )

        self._reviews[listing_id].append(review)

        listing = self._listings[listing_id]
        reviews = self._reviews[listing_id]
        listing.rating = sum(r.rating for r in reviews) / len(reviews)

        return review

    def get_reviews(self, listing_id: str) -> list[PatternReview]:
        """Get all reviews for a listing."""
        return self._reviews.get(listing_id, [])

    def export_pattern(
        self,
        listing_id: str,
        org_id: str,
    ) -> dict:
        """Export a pattern for sharing."""
        listing = self._listings.get(listing_id)
        if not listing:
            raise ValueError("Listing not found")

        if org_id != listing.owner_org and listing_id not in self._purchases.get(org_id, set()):
            raise ValueError("Not purchased")

        export_data = {
            "format_version": "1.0",
            "exported_at": datetime.now(UTC).isoformat(),
            "pattern": {
                "from_tool": listing.from_tool,
                "to_tool": listing.to_tool,
                "success_rate": listing.success_rate,
                "tags": listing.tags,
            },
            "signature": self._sign_export(listing, org_id),
        }

        return export_data

    def import_pattern(self, export_data: dict, org_id: str) -> str:
        """Import a pattern from export data."""
        if export_data.get("format_version") != "1.0":
            raise ValueError("Invalid format version")

        pattern = export_data.get("pattern", {})

        listing = self.create_listing(
            org_id=org_id,
            pattern_id=f"imported_{uuid.uuid4().hex[:8]}",
            name="Imported Pattern",
            description="Imported from marketplace",
            from_tool=pattern.get("from_tool", ""),
            to_tool=pattern.get("to_tool", ""),
            success_rate=pattern.get("success_rate", 0.0),
            tags=pattern.get("tags", []),
        )

        return listing.listing_id

    def _sign_export(self, listing: PatternListing, org_id: str) -> str:
        """Sign export data."""
        data = f"{listing.listing_id}:{org_id}:{listing.pattern_id}"
        return hashlib.sha256(data.encode()).hexdigest()

    def get_org_listings(self, org_id: str) -> list[PatternListing]:
        """Get all listings owned by an organization."""
        return [listing for listing in self._listings.values() if listing.owner_org == org_id]

    def get_statistics(self) -> dict:
        """Get marketplace statistics."""
        total_listings = len(self._listings)
        total_reviews = sum(len(r) for r in self._reviews.values())
        avg_rating = sum(listing.rating for listing in self._listings.values()) / max(
            total_listings, 1
        )

        return {
            "total_listings": total_listings,
            "total_reviews": total_reviews,
            "average_rating": avg_rating,
            "free_listings": sum(1 for listing in self._listings.values() if listing.price == 0),
            "paid_listings": sum(1 for listing in self._listings.values() if listing.price > 0),
        }
