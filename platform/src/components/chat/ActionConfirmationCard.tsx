import React, { useState } from 'react';
import {
  ShieldAlert,
  Calendar,
  Key,
  Wrench,
  FileEdit,
  Check,
  X,
  Building2,
  Clock,
  User,
  Mail,
  Phone,
  DollarSign,
  AlertTriangle
} from 'lucide-react';
import { apiClient } from '../../services/api';
import { useAppStore } from '../../stores/useAppStore';

export type ActionType = 'schedule_tour' | 'apply_lease' | 'submit_maintenance' | 'modify_lease';

export interface ActionConfirmationPayload {
  action_type: ActionType;
  prompt?: string;
  payload: Record<string, any>;
  session_id?: string;
}

interface ActionConfirmationCardProps {
  confirmation: ActionConfirmationPayload;
  sessionId?: string;
  onResolved: (finalAnswer: string) => void;
}

export const ActionConfirmationCard: React.FC<ActionConfirmationCardProps> = ({
  confirmation,
  sessionId,
  onResolved,
}) => {
  const { addToast } = useAppStore();
  const [formData, setFormData] = useState<Record<string, any>>({
    ...confirmation.payload,
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isResolved, setIsResolved] = useState(false);

  const actionType = confirmation.action_type || 'schedule_tour';

  const handleFieldChange = (key: string, value: any) => {
    setFormData((prev) => ({ ...prev, [key]: value }));
  };

  const handleDecision = async (approved: boolean) => {
    setIsSubmitting(true);
    try {
      const res = await apiClient<{ status: string; final_answer: string }>('/api/chat/action/confirm', {
        method: 'POST',
        body: JSON.stringify({
          session_id: sessionId || confirmation.session_id,
          action_type: actionType,
          payload: formData,
          approved,
        }),
      });

      setIsResolved(true);
      if (approved) {
        addToast('Action confirmed and executed successfully!', 'success');
      } else {
        addToast('Action cancelled by user.', 'info');
      }
      onResolved(res.final_answer);
    } catch (err: any) {
      addToast(err.message || 'Failed to submit action decision', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isResolved) {
    return (
      <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 text-xs flex items-center space-x-2 text-slate-400">
        <Check className="w-4 h-4 text-emerald-400" />
        <span>Action confirmation resolved and committed to record.</span>
      </div>
    );
  }

  // Visual header configs
  const headerConfig = {
    schedule_tour: {
      title: 'Human-in-the-Loop: Review Tour Booking',
      icon: <Calendar className="w-4 h-4 text-amber-400" />,
      badge: 'Tour Schedule Verification',
      border: 'border-amber-500/30',
      bg: 'bg-amber-500/10',
    },
    apply_lease: {
      title: 'Human-in-the-Loop: Review Digital Lease Application',
      icon: <Key className="w-4 h-4 text-indigo-400" />,
      badge: 'Lease Application Verification',
      border: 'border-indigo-500/30',
      bg: 'bg-indigo-500/10',
    },
    submit_maintenance: {
      title: 'Human-in-the-Loop: Review Maintenance Ticket Dispatch',
      icon: <Wrench className="w-4 h-4 text-cyan-400" />,
      badge: 'Work Order Verification',
      border: 'border-cyan-500/30',
      bg: 'bg-cyan-500/10',
    },
    modify_lease: {
      title: 'Human-in-the-Loop: Executive Lease Override Authorization',
      icon: <FileEdit className="w-4 h-4 text-purple-400" />,
      badge: 'Executive Authorization Required',
      border: 'border-purple-500/30',
      bg: 'bg-purple-500/10',
    },
  }[actionType] || {
    title: 'Human-in-the-Loop Confirmation Required',
    icon: <ShieldAlert className="w-4 h-4 text-amber-400" />,
    badge: 'Action Verification',
    border: 'border-amber-500/30',
    bg: 'bg-amber-500/10',
  };

  return (
    <div className={`p-4 sm:p-5 rounded-2xl ${headerConfig.bg} border ${headerConfig.border} space-y-4 shadow-xl`}>
      {/* Header */}
      <div className="flex items-center justify-between border-b border-white/10 pb-2.5">
        <div className="flex items-center space-x-2">
          {headerConfig.icon}
          <span className="text-xs sm:text-sm font-bold text-white">{headerConfig.title}</span>
        </div>
        <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-slate-950/80 text-slate-300 border border-white/10">
          {headerConfig.badge}
        </span>
      </div>

      <p className="text-xs text-slate-300 leading-relaxed">
        {confirmation.prompt ||
          'The autonomous assistant prepared the following action. Please review or edit the parameters below before confirming execution.'}
      </p>

      {/* Schema-Specific Editable Forms */}
      <div className="p-3.5 rounded-xl bg-slate-950/90 border border-slate-800/90 space-y-3">
        {actionType === 'schedule_tour' && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div>
              <label className="block text-[10px] font-semibold text-slate-400 mb-1">Contact Name</label>
              <input
                type="text"
                value={formData.contact_name || ''}
                onChange={(e) => handleFieldChange('contact_name', e.target.value)}
                className="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-white text-xs focus:border-indigo-500 focus:outline-none"
                placeholder="Full Name"
              />
            </div>
            <div>
              <label className="block text-[10px] font-semibold text-slate-400 mb-1">Contact Email</label>
              <input
                type="email"
                value={formData.contact_email || ''}
                onChange={(e) => handleFieldChange('contact_email', e.target.value)}
                className="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-white text-xs focus:border-indigo-500 focus:outline-none"
                placeholder="email@example.com"
              />
            </div>
            <div>
              <label className="block text-[10px] font-semibold text-slate-400 mb-1">Requested Date</label>
              <input
                type="date"
                value={formData.requested_date || '2026-08-28'}
                onChange={(e) => handleFieldChange('requested_date', e.target.value)}
                className="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-white text-xs focus:border-indigo-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-[10px] font-semibold text-slate-400 mb-1">Time Slot</label>
              <select
                value={formData.time_slot || '14:00'}
                onChange={(e) => handleFieldChange('time_slot', e.target.value)}
                className="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-white text-xs focus:border-indigo-500 focus:outline-none cursor-pointer"
              >
                <option value="10:00">10:00 AM (Morning)</option>
                <option value="12:00">12:00 PM (Noon)</option>
                <option value="14:00">02:00 PM (Afternoon)</option>
                <option value="16:30">04:30 PM (Sunset View)</option>
              </select>
            </div>
            <div className="sm:col-span-2">
              <label className="block text-[10px] font-semibold text-slate-400 mb-1">Tour Format</label>
              <div className="flex items-center space-x-4">
                <label className="flex items-center space-x-1.5 cursor-pointer">
                  <input
                    type="radio"
                    name="tour_type"
                    checked={formData.tour_type === 'in_person' || !formData.tour_type}
                    onChange={() => handleFieldChange('tour_type', 'in_person')}
                    className="text-indigo-500"
                  />
                  <span className="text-slate-300 text-xs">Accompanied In-Person</span>
                </label>
                <label className="flex items-center space-x-1.5 cursor-pointer">
                  <input
                    type="radio"
                    name="tour_type"
                    checked={formData.tour_type === 'virtual_3d'}
                    onChange={() => handleFieldChange('tour_type', 'virtual_3d')}
                    className="text-cyan-500"
                  />
                  <span className="text-slate-300 text-xs">Guided Matterport 3D Digital Twin</span>
                </label>
              </div>
            </div>
          </div>
        )}

        {actionType === 'apply_lease' && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div>
              <label className="block text-[10px] font-semibold text-slate-400 mb-1">Applicant Name</label>
              <input
                type="text"
                value={formData.applicant_name || ''}
                onChange={(e) => handleFieldChange('applicant_name', e.target.value)}
                className="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-white text-xs focus:border-indigo-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-[10px] font-semibold text-slate-400 mb-1">Proposed Monthly Rent (EGP)</label>
              <input
                type="number"
                value={formData.monthly_rent || 45000}
                onChange={(e) => handleFieldChange('monthly_rent', Number(e.target.value))}
                className="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-white text-xs font-mono focus:border-indigo-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-[10px] font-semibold text-slate-400 mb-1">Security Deposit (EGP)</label>
              <input
                type="number"
                value={formData.security_deposit || (Number(formData.monthly_rent || 45000) * 2)}
                onChange={(e) => handleFieldChange('security_deposit', Number(e.target.value))}
                className="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-white text-xs font-mono focus:border-indigo-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-[10px] font-semibold text-slate-400 mb-1">Target Move-in Date</label>
              <input
                type="date"
                value={formData.move_in_date || '2026-09-01'}
                onChange={(e) => handleFieldChange('move_in_date', e.target.value)}
                className="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-white text-xs focus:border-indigo-500 focus:outline-none"
              />
            </div>
          </div>
        )}

        {actionType === 'submit_maintenance' && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div>
              <label className="block text-[10px] font-semibold text-slate-400 mb-1">Issue Category</label>
              <select
                value={formData.category || 'plumbing'}
                onChange={(e) => handleFieldChange('category', e.target.value)}
                className="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-white text-xs focus:border-indigo-500 focus:outline-none cursor-pointer"
              >
                <option value="plumbing">Plumbing & Water</option>
                <option value="electrical">Electrical & Lighting</option>
                <option value="hvac">HVAC & Air Conditioning</option>
                <option value="structural">Structural & Carpentry</option>
                <option value="appliance">Appliance Breakdown</option>
              </select>
            </div>
            <div>
              <label className="block text-[10px] font-semibold text-slate-400 mb-1">Priority Level</label>
              <select
                value={formData.priority || 'normal'}
                onChange={(e) => handleFieldChange('priority', e.target.value)}
                className="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-white text-xs focus:border-indigo-500 focus:outline-none cursor-pointer"
              >
                <option value="normal">Normal (48h Resolution SLA)</option>
                <option value="urgent">Urgent (24h SLA)</option>
                <option value="emergency">Emergency Dispatch (4h SLA)</option>
              </select>
            </div>
            <div className="sm:col-span-2">
              <label className="block text-[10px] font-semibold text-slate-400 mb-1">Issue Description</label>
              <textarea
                rows={2}
                value={formData.description || ''}
                onChange={(e) => handleFieldChange('description', e.target.value)}
                className="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-white text-xs focus:border-indigo-500 focus:outline-none"
                placeholder="Describe the defect or repair needed..."
              />
            </div>
          </div>
        )}

        {actionType === 'modify_lease' && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div>
              <label className="block text-[10px] font-semibold text-slate-400 mb-1">Lease Reference ID</label>
              <input
                type="number"
                value={formData.lease_id || 1}
                onChange={(e) => handleFieldChange('lease_id', Number(e.target.value))}
                className="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-white text-xs font-mono focus:border-indigo-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-[10px] font-semibold text-slate-400 mb-1">Proposed Monthly Rent (EGP)</label>
              <input
                type="number"
                value={formData.proposed_rent || formData.new_rent || 42000}
                onChange={(e) => handleFieldChange('proposed_rent', Number(e.target.value))}
                className="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-white text-xs font-mono focus:border-indigo-500 focus:outline-none"
              />
            </div>
          </div>
        )}
      </div>

      {/* Decision Buttons */}
      <div className="flex items-center space-x-2.5 pt-1">
        <button
          onClick={() => handleDecision(true)}
          disabled={isSubmitting}
          className="px-4 py-2 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white flex items-center space-x-1.5 transition-all shadow-md shadow-emerald-600/20 disabled:opacity-50"
        >
          <Check className="w-3.5 h-3.5" />
          <span>{isSubmitting ? 'Executing...' : 'Approve & Execute Action'}</span>
        </button>

        <button
          onClick={() => handleDecision(false)}
          disabled={isSubmitting}
          className="px-4 py-2 rounded-xl text-xs font-bold bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/30 flex items-center space-x-1.5 transition-all disabled:opacity-50"
        >
          <X className="w-3.5 h-3.5" />
          <span>Decline / Cancel</span>
        </button>
      </div>
    </div>
  );
};
