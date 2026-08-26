// Types partages, alignes sur le schema PostgreSQL du cahier des charges

export interface Restaurant {
  id: string;
  name: string;
  currency: "USD" | "CDF";
  mobile_money_keys?: Record<string, unknown>;
  created_at: string;
}

export interface RestaurantTable {
  id: string;
  restaurant_id: string;
  number_label: string;
  capacity: number;
  zone: "VIP" | "Terrasse" | "Interieur" | string;
  status: "FREE" | "RESERVED" | "OCCUPIED" | "LOCKED";
}

export interface Reservation {
  id: string;
  restaurant_id: string;
  table_id: string | null;
  customer_name: string;
  customer_phone: string;
  reservation_date: string;
  guests_count: number;
  status:
    | "PENDING_PAYMENT"
    | "CONFIRMED"
    | "CANCELLED"
    | "COMPLETED";
  deposit_amount: number;
  qr_code_token: string;
  created_at: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "agent";
  text: string;
  timestamp: string;
}
