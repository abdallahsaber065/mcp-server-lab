import React, { useState, useEffect } from 'react';
import { X, ShieldCheck, AlertTriangle, FileSearch, ScanSearch, Users, Scale, Image as ImageIcon, Edit3, CheckCircle2, XCircle, Save, Eye } from 'lucide-react';
import { apiClient } from '../../services/api';
import { useAppStore } from '../../stores/useAppStore';

interface HITLTask {
  task_id: string;
  run_id: string;
  graph_id: string;
  node: string;
  reason: string;
  payload: any;
  created_at: string;
}

interface Props {
  task: HITLTask | null;
  onClose: () => void;
  onResolved: () => void;
}

export const HITLDetailModal: React.FC<Props> = ({ task, onClose, onResolved }) => {
  const { addToast } = useAppStore();
  const [edited, setEdited] = useState<Record<string, any>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showRaw, setShowRaw] = useState(false);
  const [notes, setNotes] = useState('');

  useEffect(() => {
    if (task) {
      setEdited({});
      setNotes('');
      setShowRaw(false);
    }
  }, [task?.task_id]);

  if (!task) return null;

  const payload = task.payload || {};
  const vision = payload.vision_extracted || payload.vision || {};
  const hasEdits = Object.keys(edited).length > 0;

  const handleField = (key: string, value: any) => {
    setEdited(prev => ({ ...prev, [key]: value }));
  };

  const getImages = (): string[] => {
    const urls: string[] = [];
    if (payload.receipt_url) urls.push(payload.receipt_url);
    if (payload.image_urls) urls.push(...(Array.isArray(payload.image_urls) ? payload.image_urls : []));
    if (payload.raw_images) urls.push(...payload.raw_images);
    if (payload.images) urls.push(...(Array.isArray(payload.images) ? payload.images : []));
    if (vision.receipt_url) urls.push(vision.receipt_url);
    // fallback demo image
    if (urls.length === 0 && task.node.includes('accountant')) {
      urls.push('/static/uploads/receipts/demo_144k.jpg');
    }
    // also check top-level image_urls from task payload
    if (payload.vision_extracted?.receipt_url) urls.push(payload.vision_extracted.receipt_url);
    return urls.filter(Boolean).slice(0, 4);
  };

  const images = getImages();

  const handleDecision = async (decision: 'approved' | 'rejected' | 'modified') => {
    setIsSubmitting(true);
    try {
      const finalDecision = hasEdits && decision === 'approved' ? 'modified' : decision;
      const updatedPayload = hasEdits ? edited : undefined;
      await apiClient(`/api/admin/hitl/tasks/${task.task_id}/resolve`, {
        method: 'POST',
        body: JSON.stringify({
          decision: finalDecision,
          notes: notes || (decision === 'approved' ? 'Approved via detailed review' : 'Rejected via detailed review'),
          updated_payload: updatedPayload,
        }),
      });
      // Also attempt to resume graph if it's a real run (not demo)
      if (!task.run_id.startsWith('demo-') && (decision === 'approved' || decision === 'modified')) {
        try {
          // Map node to variable update for resume
          const varUpdates: Record<string, any> = { ...edited };
          if (task.node.includes('accountant')) {
            varUpdates['accountant_confirmation'] = { confirmed: true, notes: notes || 'Verified' };
            // Merge vision edits
            if (edited.bank_name || edited.amount_egp || edited.depositor_name || edited.transaction_ref) {
              varUpdates['vision_extracted'] = { ...vision, ...edited };
            }
          } else if (task.node.includes('engineer')) {
            varUpdates['engineer_decision'] = 'APPROVED';
          } else if (task.node.includes('counsel')) {
            varUpdates['counsel_decision'] = 'APPROVED';
          } else if (task.node.includes('await_bank') || task.node.includes('execute')) {
            varUpdates['hitl_decision'] = 'APPROVED';
          }
          // Only call if we have a run_id
          if (task.run_id) {
            await apiClient('/api/state-graph/run', {
              method: 'POST',
              body: JSON.stringify({ graph_id: task.graph_id, run_id: task.run_id, variables: varUpdates }),
            });
          }
        } catch (e) {
          console.warn('Graph resume after HITL (non-critical):', e);
        }
      }
      addToast(`Task ${task.task_id} ${finalDecision} successfully`, decision === 'approved' ? 'success' : 'info');
      onResolved();
      onClose();
    } catch (err: any) {
      addToast(err.message || 'Failed to resolve task', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const isAccountant = task.node.includes('accountant') || task.node.includes('verify_receipt');
  const isEngineer = task.node.includes('engineer');
  const isCounsel = task.node.includes('counsel');
  const isExecutive = task.node.includes('await_bank') || task.node.includes('execute') || task.graph_id.includes('commercial_lease');

  // Helper to get field value (edited or original)
  const getVal = (key: string, fallback: any) => edited[key] !== undefined ? edited[key] : fallback;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-4xl max-h-[90vh] overflow-hidden rounded-2xl border border-slate-700 bg-slate-900 shadow-2xl flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-start justify-between bg-gradient-to-r from-indigo-950/40 to-slate-900/60">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <div className={`w-8 h-8 rounded-xl flex items-center justify-center border ${isAccountant ? 'bg-amber-500/20 border-amber-500/30' : isEngineer ? 'bg-cyan-500/20 border-cyan-500/30' : isCounsel ? 'bg-violet-500/20 border-violet-500/30' : 'bg-indigo-500/20 border-indigo-500/30'}`}>
                {isAccountant ? <FileSearch className="w-4 h-4 text-amber-400" /> : isEngineer ? <Users className="w-4 h-4 text-cyan-400" /> : isCounsel ? <Scale className="w-4 h-4 text-violet-400" /> : <ShieldCheck className="w-4 h-4 text-indigo-400" />}
              </div>
              <div>
                <div className="text-sm font-bold text-slate-100">{task.node} — {task.graph_id}</div>
                <div className="text-[11px] text-slate-400 font-mono">Task {task.task_id} • Run {task.run_id} • {new Date(task.created_at).toLocaleString()}</div>
              </div>
            </div>
            <div className="text-xs text-slate-300 bg-slate-950/60 rounded-xl p-3 border border-slate-800 mt-2" dir={task.reason.includes('محاسب') || task.reason.includes('مهندس') ? 'rtl' : undefined}>{task.reason}</div>
          </div>
          <button onClick={onClose} className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Accountant: Images + Vision Form */}
          {isAccountant && (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Raw Images Gallery */}
                <div className="space-y-3">
                  <h3 className="text-xs font-bold text-slate-200 flex items-center gap-2"><ImageIcon className="w-4 h-4 text-amber-400" /> الصور الأصلية — Raw Images Gallery</h3>
                  {images.length > 0 ? (
                    <div className="grid grid-cols-2 gap-3">
                      {images.map((url, i) => (
                        <a key={i} href={url} target="_blank" rel="noopener noreferrer" className="group relative rounded-xl overflow-hidden border border-slate-700 bg-slate-950 aspect-[4/3] flex items-center justify-center">
                          <img src={url} alt={`Receipt ${i + 1}`} className="w-full h-full object-cover group-hover:scale-105 transition-transform" onError={(e) => (e.currentTarget.style.display = 'none')} />
                          <div className="absolute bottom-1 right-1 text-[10px] px-1.5 py-0.5 rounded bg-slate-900/80 text-slate-300 border border-slate-700">#{i + 1}</div>
                          <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-center justify-center opacity-0 group-hover:opacity-100">
                            <Eye className="w-6 h-6 text-white" />
                          </div>
                        </a>
                      ))}
                    </div>
                  ) : (
                    <div className="p-6 border border-dashed border-slate-700 rounded-xl text-center text-xs text-slate-500">No images attached — upload will appear here for visual inspection</div>
                  )}
                  <div className="text-[11px] text-slate-500">قارن الصورة مع البيانات المستخرجة على اليمين — أي اختلاف يجب تعديله قبل التأكيد.</div>
                </div>

                {/* AI-Extracted Editable Form */}
                <div className="space-y-3">
                  <h3 className="text-xs font-bold text-slate-200 flex items-center gap-2"><ScanSearch className="w-4 h-4 text-cyan-400" /> البيانات المستخرجة — AI-Extracted (Gemini Vision) — قابل للتعديل</h3>
                  <div className="space-y-3 bg-slate-950/60 rounded-xl p-4 border border-slate-800">
                    {[
                      { key: 'bank_name', label: 'اسم البنك', fallback: vision.bank_name || payload.bank_name || 'Banque Misr', type: 'text' },
                      { key: 'depositor_name', label: 'اسم المودع', fallback: vision.depositor_name || payload.depositor_name || vision.depositor || 'Ahmed Corporate LLC', type: 'text' },
                      { key: 'amount_egp', label: 'المبلغ (ج.م)', fallback: vision.amount_egp || vision.amount || payload.amount_egp || 144000, type: 'number' },
                      { key: 'transaction_ref', label: 'الرقم المرجعي', fallback: vision.transaction_ref || payload.transaction_ref || vision.transaction_reference || 'BM-DEMO-144K', type: 'text' },
                      { key: 'receipt_date', label: 'تاريخ الإيصال', fallback: vision.receipt_date || '2026-08-22', type: 'date' },
                    ].map(f => (
                      <div key={f.key}>
                        <label className="block text-[11px] text-slate-400 mb-1">{f.label}</label>
                        <div className="relative">
                          <input
                            type={f.type}
                            value={getVal(f.key, f.fallback)}
                            onChange={e => handleField(f.key, f.type === 'number' ? Number(e.target.value) : e.target.value)}
                            className={`w-full bg-slate-900 border rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none ${edited[f.key] !== undefined ? 'border-amber-500/50 bg-amber-950/20' : 'border-slate-700 focus:border-indigo-500'}`}
                          />
                          {edited[f.key] !== undefined && <Edit3 className="w-3 h-3 text-amber-400 absolute right-2.5 top-2.5" />}
                        </div>
                      </div>
                    ))}
                    <div>
                      <label className="block text-[11px] text-slate-400 mb-1">ملاحظات المحاسب</label>
                      <textarea value={notes} onChange={e => setNotes(e.target.value)} rows={2} placeholder="مثال: تمت المطابقة مع كشف الحساب البنكي" className="w-full bg-slate-900 border border-slate-700 rounded-xl p-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500" />
                    </div>
                    {hasEdits && <div className="text-[11px] text-amber-300 bg-amber-950/30 border border-amber-500/30 rounded-xl p-2 flex items-center gap-1"><Edit3 className="w-3 h-3" /> تم تعديل {Object.keys(edited).length} حقول — سيتم الحفظ كـ "modified" عند الموافقة</div>}
                  </div>
                </div>
              </div>
              <div className="bg-indigo-950/20 border border-indigo-500/20 rounded-xl p-3 text-xs text-indigo-200">
                <span className="font-bold">ماذا سيحدث بعد الموافقة؟</span> سيتم تسجيل <code className="bg-slate-900 px-1 rounded">accountant_confirmation: confirmed</code> والمتابعة إلى بوابة الحجز المصرفي (Bank Escrow) ثم موافقة المدير التنفيذي إذا الخصم &gt;15%.
              </div>
            </>
          )}

          {/* Engineer */}
          {isEngineer && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-slate-950/60 rounded-xl p-4 border border-slate-800 space-y-3">
                  <h3 className="text-xs font-bold text-slate-200 flex items-center gap-2"><Users className="w-4 h-4 text-cyan-400" /> تفاصيل أمر الشغل</h3>
                  {[
                    { key: 'estimate', label: 'التكلفة التقديرية (ج.م)', fallback: payload.estimate || payload.vendor_sla_matrix?.estimate || 18500, type: 'number' },
                    { key: 'contractor', label: 'المقاول المقترح (LATS)', fallback: payload.contractor || payload.vendor_sla_matrix?.vendor_name || 'Nile Specialized Engineering & Maintenance', type: 'text' },
                  ].map(f => (
                    <div key={f.key}>
                      <label className="block text-[11px] text-slate-400 mb-1">{f.label}</label>
                      <input type={f.type} value={getVal(f.key, f.fallback)} onChange={e => handleField(f.key, f.type === 'number' ? Number(e.target.value) : e.target.value)} className={`w-full bg-slate-900 border rounded-xl px-3 py-2 text-xs text-slate-200 ${edited[f.key] !== undefined ? 'border-amber-500/50 bg-amber-950/20' : 'border-slate-700'}`} />
                    </div>
                  ))}
                  {payload.vendor_sla_matrix && (
                    <div className="p-3 rounded-xl bg-slate-900 border border-slate-700">
                      <div className="text-[11px] font-bold text-slate-300 mb-1">مصفوفة التقييم LATS</div>
                      <div className="text-[11px] text-slate-400 font-mono">SLA: {payload.vendor_sla_matrix.dispatch_sla_hours}h • الالتزام: {payload.vendor_sla_matrix.sla_compliance_pct}% • النتيجة: {payload.vendor_sla_matrix.composite_score}</div>
                    </div>
                  )}
                </div>
                <div className="bg-slate-950/60 rounded-xl p-4 border border-slate-800">
                  <h3 className="text-xs font-bold text-slate-200">الوثائق المسترجعة (RAG)</h3>
                  <div className="text-[11px] text-slate-400 mt-2">قانون 4/1996، حد 10,000 ج.م للموافقة، مهلة 2 ساعة للطوارئ</div>
                  <div className="mt-3">
                    <label className="block text-[11px] text-slate-400 mb-1">ملاحظات المهندس</label>
                    <textarea value={notes} onChange={e => setNotes(e.target.value)} rows={3} placeholder="مطابق للمواصفات / تعديل التكلفة..." className="w-full bg-slate-900 border border-slate-700 rounded-xl p-2 text-xs text-slate-200" />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Counsel / Executive */}
          {(isCounsel || isExecutive) && !isAccountant && !isEngineer && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-slate-950/60 rounded-xl p-4 border border-slate-800 space-y-3">
                  <h3 className="text-xs font-bold text-slate-200 flex items-center gap-2"><Scale className="w-4 h-4 text-violet-400" /> تفاصيل التسوية / الخصم</h3>
                  {isCounsel ? (
                    <>
                      {[
                        { key: 'arrears', label: 'إجمالي المتأخرات (ج.م)', fallback: payload.arrears || payload.plan?.arrears || 120000, type: 'number' },
                        { key: 'installments_count', label: 'عدد الأقساط', fallback: payload.plan?.installments_count || 6, type: 'number' },
                        { key: 'monthly_installment', label: 'القسط الشهري (ج.م)', fallback: payload.plan?.monthly_installment || 20000, type: 'number' },
                      ].map(f => (
                        <div key={f.key}>
                          <label className="block text-[11px] text-slate-400 mb-1">{f.label}</label>
                          <input type={f.type} value={getVal(f.key, f.fallback)} onChange={e => handleField(f.key, Number(e.target.value))} className={`w-full bg-slate-900 border rounded-xl px-3 py-2 text-xs text-slate-200 ${edited[f.key] !== undefined ? 'border-amber-500/50 bg-amber-950/20' : 'border-slate-700'}`} />
                        </div>
                      ))}
                    </>
                  ) : (
                    <>
                      {[
                        { key: 'proposed_rent', label: 'الإيجار المقترح (ج.م)', fallback: payload.proposed_rent || 48000, type: 'number' },
                        { key: 'discount_pct', label: 'نسبة الخصم %', fallback: payload.discount_pct || 20, type: 'number' },
                        { key: 'unit_id', label: 'رقم الوحدة', fallback: payload.unit_id || 301, type: 'number' },
                      ].map(f => (
                        <div key={f.key}>
                          <label className="block text-[11px] text-slate-400 mb-1">{f.label}</label>
                          <input type={f.type} value={getVal(f.key, f.fallback)} onChange={e => handleField(f.key, Number(e.target.value))} className={`w-full bg-slate-900 border rounded-xl px-3 py-2 text-xs text-slate-200 ${edited[f.key] !== undefined ? 'border-amber-500/50 bg-amber-950/20' : 'border-slate-700'}`} />
                        </div>
                      ))}
                    </>
                  )}
                </div>
                <div className="bg-slate-950/60 rounded-xl p-4 border border-slate-800">
                  <h3 className="text-xs font-bold text-slate-200">السياق القانوني</h3>
                  <div className="text-[11px] text-slate-400 mt-2">المادة 586، مهلة 14 يوم، حد خصم 15% للموافقة التنفيذية</div>
                  <div className="mt-3">
                    <label className="block text-[11px] text-slate-400 mb-1">ملاحظات القرار</label>
                    <textarea value={notes} onChange={e => setNotes(e.target.value)} rows={3} placeholder="أسباب الموافقة/الرفض..." className="w-full bg-slate-900 border border-slate-700 rounded-xl p-2 text-xs text-slate-200" />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Generic fallback: JSON editor */}
          {!isAccountant && !isEngineer && !isCounsel && !isExecutive && (
            <div className="space-y-3">
              <h3 className="text-xs font-bold text-slate-200">تفاصيل المهمة (JSON)</h3>
              <pre className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-[11px] text-slate-300 font-mono overflow-auto max-h-64">{JSON.stringify(payload, null, 2)}</pre>
              <div>
                <label className="block text-[11px] text-slate-400 mb-1">ملاحظات</label>
                <textarea value={notes} onChange={e => setNotes(e.target.value)} rows={2} className="w-full bg-slate-900 border border-slate-700 rounded-xl p-2 text-xs text-slate-200" />
              </div>
            </div>
          )}

          {/* Raw toggle */}
          <div className="flex items-center gap-2">
            <button onClick={() => setShowRaw(!showRaw)} className="text-[11px] px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 flex items-center gap-1">
              <Eye className="w-3 h-3" /> {showRaw ? 'إخفاء الخام' : 'عرض الخام JSON'}
            </button>
            {hasEdits && <span className="text-[11px] text-amber-300 flex items-center gap-1"><Edit3 className="w-3 h-3" /> {Object.keys(edited).length} تعديلات</span>}
          </div>
          {showRaw && <pre className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-[11px] text-slate-400 font-mono overflow-auto max-h-48">{JSON.stringify({ task, edited }, null, 2)}</pre>}
        </div>

        {/* Footer actions */}
        <div className="px-6 py-4 border-t border-slate-800 bg-slate-950/60 flex flex-wrap gap-2 justify-between">
          <button onClick={() => handleDecision('rejected')} disabled={isSubmitting} className="px-4 py-2 rounded-xl text-xs font-semibold bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-white flex items-center gap-1.5">
            <XCircle className="w-4 h-4" /> رفض
          </button>
          <div className="flex gap-2">
            <button onClick={onClose} disabled={isSubmitting} className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700">إلغاء</button>
            <button onClick={() => handleDecision('approved')} disabled={isSubmitting} className={`px-5 py-2 rounded-xl text-xs font-bold flex items-center gap-1.5 ${hasEdits ? 'bg-amber-600 hover:bg-amber-500 text-white' : 'bg-emerald-600 hover:bg-emerald-500 text-white'} disabled:opacity-50`}>
              {hasEdits ? <Save className="w-4 h-4" /> : <CheckCircle2 className="w-4 h-4" />}
              {hasEdits ? 'اعتماد بالتعديلات' : 'اعتماد الكل'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
