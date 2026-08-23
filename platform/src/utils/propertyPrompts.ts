/**
 * Real Estate Natural Language Assistant Prompts (platform/src/utils/propertyPrompts.ts)
 * Structured prompts crafted for the Cornerstone AI Leasing & Operations Agent.
 */

export interface PropertyPromptContext {
  property_id: number;
  name: string;
  address: string;
  city: string;
  neighborhood?: string;
  property_type?: string;
  total_units?: number;
  available_units?: number;
  starting_rent?: number;
  amenities?: string[];
}

export interface UnitPromptContext {
  unit_id?: number;
  unit_number: string;
  title?: string;
  bedrooms?: number;
  bathrooms?: number;
  square_feet?: number;
  monthly_rent: number;
  status?: string;
  features?: string[] | string;
}

/**
 * Generate a comprehensive prompt to apply for a tenancy lease on a specific unit.
 */
export function generateApplyPrompt(property: PropertyPromptContext, unit: UnitPromptContext): string {
  const deposit = unit.monthly_rent ? (unit.monthly_rent * 2).toLocaleString() : 'N/A';
  const rent = unit.monthly_rent ? unit.monthly_rent.toLocaleString() : 'N/A';
  const location = property.neighborhood ? `${property.neighborhood}, ${property.city}` : `${property.address}, ${property.city}`;

  return `I would like to apply for a verified tenancy lease for ${unit.title || `Unit ${unit.unit_number}`} (${unit.unit_number}) at ${property.name}, located at ${location}.

Listing Details:
• Property: ${property.name} (${property.address})
• Unit: ${unit.unit_number} (${unit.bedrooms || 1} Bed, ${unit.bathrooms || 1} Bath, ${unit.square_feet || 150} m²)
• Listed Monthly Rent: ${rent} EGP / month
• Security Deposit: ${deposit} EGP (2 months)

Please verify current unit availability, outline required tenant identity documents, and guide me through drafting the formal tenancy agreement.`;
}

/**
 * Generate a prompt to schedule an in-person or 3D Matterport guided viewing tour.
 */
export function generateTourPrompt(
  property: PropertyPromptContext,
  unit?: UnitPromptContext,
  tourType: 'in_person' | 'virtual_3d' = 'in_person'
): string {
  const tourFormat = tourType === 'virtual_3d' ? '3D Matterport interactive digital walkthrough' : 'private accompanied in-person viewing';
  const unitSpec = unit ? ` specifically for Suite ${unit.unit_number} (${unit.title || ''})` : '';
  const location = property.neighborhood ? `${property.neighborhood}, ${property.city}` : `${property.address}, ${property.city}`;

  return `I would like to schedule a ${tourFormat} for ${property.name}${unitSpec}, located at ${location}.

Please check available appointment time slots for this week, explain the viewing process, and assist me in reserving a confirmed tour booking.`;
}

/**
 * Generate a prompt for Property Managers to audit and control unit inventory.
 */
export function generateManagerUnitsPrompt(property: PropertyPromptContext): string {
  return `Please open property management control for ${property.name} (Property ID #${property.property_id}, located at ${property.address}, ${property.city}).

Provide a breakdown of all units, their current lease statuses (available, occupied, maintenance), monthly rental yields, and high-value asset classifications.`;
}

/**
 * Generate a prompt for Property Managers to review and manage viewing tour appointments.
 */
export function generateManagerToursPrompt(property: PropertyPromptContext): string {
  return `Retrieve all scheduled viewing appointments and pending prospect tour bookings for ${property.name} (Property ID #${property.property_id}).

Show candidate names, contact details, requested dates, and help me approve, reschedule, or complete these tour reservations.`;
}

/**
 * Generate a prompt to inquire about full property specifications and amenities.
 */
export function generatePropertyInquiryPrompt(property: PropertyPromptContext): string {
  const location = property.neighborhood ? `${property.neighborhood}, ${property.city}` : `${property.address}, ${property.city}`;
  return `Please provide a comprehensive dossier on ${property.name} in ${location}.

Include architectural specifications, curated resident amenities, available floor plans, and starting lease rates.`;
}
