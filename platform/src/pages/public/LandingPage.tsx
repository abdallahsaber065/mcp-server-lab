/**
 * Modern Luxury Real Estate Marketing Landing Page (platform/src/pages/public/LandingPage.tsx)
 * Assembled from structured marketing components for enterprise appeal.
 */

import React, { useState } from 'react';
import { MarketingHero } from '../../components/landing/MarketingHero';
import { FeaturedProperties } from '../../components/landing/FeaturedProperties';
import { NeighborhoodShowcase } from '../../components/landing/NeighborhoodShowcase';
import { ConciergeServices } from '../../components/landing/ConciergeServices';
import { TestimonialSection } from '../../components/landing/TestimonialSection';
import { VipInquiryCta } from '../../components/landing/VipInquiryCta';
import { ScheduleTourModal } from '../../components/properties/ScheduleTourModal';
import { PropertyDetailModal } from '../../components/properties/PropertyDetailModal';

export const LandingPage: React.FC = () => {
  const [selectedPropertyId, setSelectedPropertyId] = useState<number | null>(null);
  const [isScheduleModalOpen, setIsScheduleModalOpen] = useState<boolean>(false);
  const [schedulePropertyId, setSchedulePropertyId] = useState<number | undefined>(undefined);

  const handleOpenScheduleModal = (propId?: number) => {
    setSchedulePropertyId(propId);
    setIsScheduleModalOpen(true);
  };

  const handleSelectProperty = (propId: number) => {
    setSelectedPropertyId(propId);
  };

  return (
    <div className="space-y-16 pb-20">
      {/* 1. Marketing Hero with Real Estate Discovery Search */}
      <MarketingHero onOpenScheduleModal={handleOpenScheduleModal} />

      {/* 2. Curated Featured Luxury Residences */}
      <FeaturedProperties
        onSelectProperty={handleSelectProperty}
        onOpenScheduleModal={handleOpenScheduleModal}
      />

      {/* 3. Egypt's Prime Neighborhoods Explorer */}
      <NeighborhoodShowcase />

      {/* 4. Autonomous Property Management & AI Concierge */}
      <ConciergeServices />

      {/* 5. Resident & Diplomatic Testimonials */}
      <TestimonialSection />

      {/* 6. VIP Off-Market Portfolio CTA */}
      <VipInquiryCta onOpenScheduleModal={() => handleOpenScheduleModal()} />

      {/* Interactive Modals */}
      <ScheduleTourModal
        isOpen={isScheduleModalOpen}
        onClose={() => setIsScheduleModalOpen(false)}
        propertyId={schedulePropertyId}
      />

      <PropertyDetailModal
        propertyId={selectedPropertyId}
        onClose={() => setSelectedPropertyId(null)}
        onOpenScheduleModal={handleOpenScheduleModal}
      />
    </div>
  );
};
