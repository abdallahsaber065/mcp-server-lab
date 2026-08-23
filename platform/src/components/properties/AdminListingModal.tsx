import React, { useState } from 'react';
import { X, Plus, Building, Bed, DollarSign, CheckCircle2, Image as ImageIcon } from 'lucide-react';
import { apiClient } from '../../services/api';

interface AdminListingModalProps {
  isOpen: boolean;
  onClose: () => void;
  properties: any[];
  onRefresh: () => void;
}

export const AdminListingModal: React.FC<AdminListingModalProps> = ({
  isOpen,
  onClose,
  properties,
  onRefresh
}) => {
  const [tab, setTab] = useState<'property' | 'unit'>('property');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Property Form State
  const [name, setName] = useState('');
  const [address, setAddress] = useState('');
  const [city, setCity] = useState('Cairo');
  const [neighborhood, setNeighborhood] = useState('');
  const [propertyType, setPropertyType] = useState('luxury_residential');
  const [description, setDescription] = useState('');
  const [imageUrl, setImageUrl] = useState('/images/properties/nile_tower_ext.jpg');
  const [amenitiesStr, setAmenitiesStr] = useState('24/7 Concierge, Infinity Pool, Valet Parking, Private Elevator');
  const [yearBuilt, setYearBuilt] = useState<number>(2024);
  const [isFeatured, setIsFeatured] = useState<boolean>(true);

  // Unit Form State
  const [targetPropertyId, setTargetPropertyId] = useState<number>(properties[0]?.property_id || 1);
  const [unitNumber, setUnitNumber] = useState('');
  const [unitTitle, setUnitTitle] = useState('');
  const [unitDesc, setUnitDesc] = useState('');
  const [unitRent, setUnitRent] = useState<number>(35000);
  const [bedrooms, setBedrooms] = useState<number>(2);
  const [bathrooms, setBathrooms] = useState<number>(2.0);
  const [squareFeet, setSquareFeet] = useState<number>(180);
  const [floorNumber, setFloorNumber] = useState<number>(5);
  const [featuresStr, setFeaturesStr] = useState('Panoramic Balcony, Smart AC, Walk-in Closet');

  if (!isOpen) return null;

  const handleCreateProperty = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const amenities = amenitiesStr.split(',').map((s) => s.trim()).filter(Boolean);
      await apiClient('/api/properties', {
        method: 'POST',
        body: JSON.stringify({
          name,
          address,
          city,
          neighborhood: neighborhood || city,
          property_type: propertyType,
          description,
          image_url: imageUrl,
          amenities,
          year_built: Number(yearBuilt),
          is_featured: isFeatured
        })
      });
      setSuccessMsg(`Property '${name}' created successfully!`);
      onRefresh();
      setTimeout(() => {
        setSuccessMsg(null);
        onClose();
      }, 1500);
    } catch (err: any) {
      alert(`Error creating property: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCreateUnit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const features = featuresStr.split(',').map((s) => s.trim()).filter(Boolean);
      await apiClient('/api/properties/units', {
        method: 'POST',
        body: JSON.stringify({
          property_id: Number(targetPropertyId),
          unit_number: unitNumber,
          title: unitTitle || `Unit ${unitNumber}`,
          description: unitDesc,
          monthly_rent: Number(unitRent),
          bedrooms: Number(bedrooms),
          bathrooms: Number(bathrooms),
          square_feet: Number(squareFeet),
          floor_number: Number(floorNumber),
          features,
          status: 'available',
          is_high_value: Number(unitRent) >= 40000
        })
      });
      setSuccessMsg(`Unit '${unitNumber}' added successfully!`);
      onRefresh();
      setTimeout(() => {
        setSuccessMsg(null);
        onClose();
      }, 1500);
    } catch (err: any) {
      alert(`Error creating unit: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="glass-card w-full max-w-2xl p-6 sm:p-8 rounded-3xl border-slate-700 shadow-2xl relative max-h-[90vh] overflow-y-auto">
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="space-y-4">
          <div>
            <div className="inline-flex items-center space-x-2 text-xs font-bold text-indigo-400 uppercase tracking-wider mb-1">
              <Building className="w-3.5 h-3.5" />
              <span>Asset Management Portal</span>
            </div>
            <h3 className="text-xl font-bold text-white">Create New Real Estate Listing</h3>
            <p className="text-xs text-slate-400">Add high-value residential properties or individual suites to the directory.</p>
          </div>

          {/* Tab Switcher */}
          <div className="flex p-1 bg-slate-900 rounded-xl border border-slate-800">
            <button
              onClick={() => setTab('property')}
              className={`flex-1 py-2 rounded-lg text-xs font-bold transition-all ${
                tab === 'property' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:text-white'
              }`}
            >
              1. Add New Property / Building
            </button>
            <button
              onClick={() => setTab('unit')}
              className={`flex-1 py-2 rounded-lg text-xs font-bold transition-all ${
                tab === 'unit' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:text-white'
              }`}
            >
              2. Add Suite / Unit to Building
            </button>
          </div>

          {successMsg && (
            <div className="p-4 rounded-xl bg-emerald-950/60 border border-emerald-500/30 text-emerald-300 text-xs flex items-center space-x-2 font-semibold">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>{successMsg}</span>
            </div>
          )}

          {tab === 'property' ? (
            <form onSubmit={handleCreateProperty} className="space-y-4 pt-2">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-300">Property Name</label>
                  <input
                    type="text"
                    placeholder="e.g. Nile Crown Luxury Residences"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-300">Property Type</label>
                  <select
                    value={propertyType}
                    onChange={(e) => setPropertyType(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                  >
                    <option value="luxury_residential">Luxury Residential</option>
                    <option value="heritage_residential">Heritage Residential</option>
                    <option value="resort_residential">Resort / Beachfront</option>
                    <option value="commercial_office">Commercial Office</option>
                    <option value="residential_compound">Gated Compound</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-300">City</label>
                  <select
                    value={city}
                    onChange={(e) => setCity(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                  >
                    <option value="Cairo">Cairo</option>
                    <option value="New Cairo">New Cairo</option>
                    <option value="Giza">Giza</option>
                    <option value="Sheikh Zayed">Sheikh Zayed</option>
                    <option value="Alexandria">Alexandria</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-300">Neighborhood / District</label>
                  <input
                    type="text"
                    placeholder="e.g. Garden City Waterfront"
                    value={neighborhood}
                    onChange={(e) => setNeighborhood(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-300">Year Built</label>
                  <input
                    type="number"
                    value={yearBuilt}
                    onChange={(e) => setYearBuilt(Number(e.target.value))}
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-300">Full Street Address</label>
                <input
                  type="text"
                  placeholder="e.g. 24 Corniche El Nile, Garden City, Cairo"
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  required
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-300">Featured Image Local Path / URL</label>
                <select
                  value={imageUrl}
                  onChange={(e) => setImageUrl(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                >
                  <option value="/images/properties/nile_tower_ext.jpg">Nile Tower Sky Exterior</option>
                  <option value="/images/properties/zamalek_ext.jpg">Zamalek Heritage Exterior</option>
                  <option value="/images/properties/alexandria_ext.jpg">Alexandria Beachfront Exterior</option>
                  <option value="/images/properties/giza_ext.jpg">Giza Pyramids View Estate</option>
                  <option value="/images/properties/new_cairo_ext.jpg">New Cairo Modern Villa</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-300">Architectural Description</label>
                <textarea
                  rows={2}
                  placeholder="Exquisite luxury property overlooking..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-300">Building Amenities (Comma-separated)</label>
                <input
                  type="text"
                  value={amenitiesStr}
                  onChange={(e) => setAmenitiesStr(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full py-3 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg transition-all"
              >
                {isSubmitting ? 'Creating Listing...' : 'Publish Property Listing'}
              </button>
            </form>
          ) : (
            <form onSubmit={handleCreateUnit} className="space-y-4 pt-2">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-300">Target Building</label>
                  <select
                    value={targetPropertyId}
                    onChange={(e) => setTargetPropertyId(Number(e.target.value))}
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                  >
                    {properties.map((p) => (
                      <option key={p.property_id} value={p.property_id}>
                        {p.name} ({p.city})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-300">Unit Number / Code</label>
                  <input
                    type="text"
                    placeholder="e.g. PH-02-Nile"
                    value={unitNumber}
                    onChange={(e) => setUnitNumber(e.target.value)}
                    required
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-300">Suite Title</label>
                <input
                  type="text"
                  placeholder="e.g. Royal Corner Penthouse with Private Terrace"
                  value={unitTitle}
                  onChange={(e) => setUnitTitle(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-300">Monthly Rent (EGP)</label>
                  <input
                    type="number"
                    value={unitRent}
                    onChange={(e) => setUnitRent(Number(e.target.value))}
                    required
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-300">Bedrooms</label>
                  <input
                    type="number"
                    value={bedrooms}
                    onChange={(e) => setBedrooms(Number(e.target.value))}
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-300">Bathrooms</label>
                  <input
                    type="number"
                    step="0.5"
                    value={bathrooms}
                    onChange={(e) => setBathrooms(Number(e.target.value))}
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-300">Size (m²)</label>
                  <input
                    type="number"
                    value={squareFeet}
                    onChange={(e) => setSquareFeet(Number(e.target.value))}
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-300">Unit Features (Comma-separated)</label>
                <input
                  type="text"
                  value={featuresStr}
                  onChange={(e) => setFeaturesStr(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full py-3 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg transition-all"
              >
                {isSubmitting ? 'Adding Unit...' : 'Add Suite to Building'}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};
