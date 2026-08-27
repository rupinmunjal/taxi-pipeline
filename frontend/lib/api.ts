export interface DateRangeParams {
  startDate?: string;
  endDate?: string;
}

export interface RevenueByWeekday {
  weekday: string;
  avg_revenue: number;
}

export interface DurationByWeekday {
  weekday: string;
  avg_trip_duration: number;
}

export interface TopZone {
  zone_id: number;
  revenue: number;
}

export interface Summary {
  total_trips: number;
  total_revenue: number;
  avg_fare: number;
}

const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

function queryString(range: DateRangeParams): string {
  if (!range.startDate || !range.endDate) return "";
  const params = new URLSearchParams({
    start_date: range.startDate,
    end_date: range.endDate,
  });
  return `?${params.toString()}`;
}

async function request<T>(path: string, range: DateRangeParams, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${API_URL}${path}${queryString(range)}`, {
    signal,
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`API request failed with status ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function fetchRevenueByWeekday(range: DateRangeParams, signal?: AbortSignal) {
  return request<RevenueByWeekday[]>("/api/revenue-by-weekday", range, signal);
}

export function fetchDurationByWeekday(range: DateRangeParams, signal?: AbortSignal) {
  return request<DurationByWeekday[]>("/api/duration-by-weekday", range, signal);
}

export function fetchTopZones(range: DateRangeParams, signal?: AbortSignal) {
  return request<TopZone[]>("/api/top-zones", range, signal);
}

export function fetchSummary(range: DateRangeParams, signal?: AbortSignal) {
  return request<Summary>("/api/summary", range, signal);
}
