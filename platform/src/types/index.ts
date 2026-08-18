export type UserRole = 'tenant' | 'property_manager' | 'executive_admin' | 'public';

export interface User {
  id: number;
  tenant_id?: number;
  full_name: string;
  email: string;
  role: UserRole;
  phone?: string;
  assigned_unit_id?: number | null;
}

export interface Property {
  property_id: number;
  name: string;
  address: string;
  city: string;
  property_type: string;
  total_units: number;
  occupancy_rate: number;
}

export interface Unit {
  unit_id: number;
  property_id: number;
  property_name: string;
  city: string;
  unit_number: string;
  bedrooms: number;
  monthly_rent: number;
  is_high_value: boolean;
  status: string;
}

export interface Lease {
  lease_id: number;
  tenant_id?: number;
  tenant_name?: string;
  tenant_email?: string;
  property_name: string;
  unit_number: string;
  monthly_rent: number;
  start_date: string;
  end_date: string;
  payment_status: 'current' | 'pending' | 'arrears' | 'disputed';
  is_active: boolean;
  requires_executive_signoff: boolean;
  notes?: string;
}

export interface MaintenanceRequest {
  request_id: number;
  unit_id: number;
  unit_number: string;
  property_name: string;
  tenant_name?: string;
  issue_type: string;
  priority: 'emergency' | 'high' | 'medium' | 'low';
  description: string;
  status: 'open' | 'dispatched' | 'in_progress' | 'resolved' | 'cancelled';
  estimated_cost: number;
  contractor_name?: string;
  submitted_at: string;
}

export interface StateGraphNode {
  id: string;
  label: string;
  description: string;
  status?: 'pending' | 'active' | 'completed' | 'paused' | 'failed';
  data?: Record<string, any>;
}

export interface HITLTask {
  task_id: string;
  run_id: string;
  graph_id: string;
  node: string;
  reason: string;
  payload: Record<string, any>;
  created_at: string;
}

export interface FailureTicket {
  ticket_id: string;
  run_id: string;
  graph_id: string;
  node: string;
  error_type: string;
  message: string;
  status: 'open' | 'investigating' | 'resolved';
  created_at: string;
}

export interface ToolBinding {
  name: string;
  description: string;
  is_enabled: boolean;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant' | 'system' | 'tool';
  content?: string;
  text?: string;
  created_at?: string;
  timestamp?: string;
  intent?: {
    type: string;
    rationale: string;
  };
  subtasks?: Array<{
    instruction: string;
    method: string;
    output: string;
    status?: string;
  }>;
  toolTraces?: Array<{
    tool: string;
    args: any;
    result: any;
    status?: string;
  }>;
  elicitation?: {
    prompt: string;
    lease_id?: number;
    proposed_rent?: number;
  };
  selfRag?: {
    is_relevant?: boolean;
    is_supported?: boolean;
    score?: number;
    citations?: string[];
  };
  memory?: {
    type?: string;
    fact?: string;
    action?: string;
  };
}
