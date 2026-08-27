"use client";

import { Card, DateRangePicker, type DateRangePickerValue } from "@tremor/react";
import { useEffect, useState } from "react";

import { DurationByWeekdayChart } from "@/components/DurationByWeekdayChart";
import { RevenueByWeekdayChart } from "@/components/RevenueByWeekdayChart";
import { TopZonesTable } from "@/components/TopZonesTable";
import {
  fetchDurationByWeekday,
  fetchRevenueByWeekday,
  fetchSummary,
  fetchTopZones,
  type DurationByWeekday,
  type RevenueByWeekday,
  type Summary,
  type TopZone,
} from "@/lib/api";

type LoadState<T> = {
  data: T;
  loading: boolean;
  error: string | null;
};

const emptySummary: Summary = { total_trips: 0, total_revenue: 0, avg_fare: 0 };

function formatDate(value: Date): string {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

function StatCard({ label, value, loading }: { label: string; value: string; loading: boolean }) {
  return (
    <Card className="rounded-2xl border-zinc-200 shadow-sm">
      <p className="text-sm font-medium text-zinc-500">{label}</p>
      {loading ? (
        <div className="mt-3 h-9 w-32 animate-pulse rounded-lg bg-zinc-200" />
      ) : (
        <p className="mt-2 font-mono text-3xl font-semibold tracking-tight text-zinc-950">
          {value}
        </p>
      )}
    </Card>
  );
}

export default function Home() {
  const [range, setRange] = useState<DateRangePickerValue>({});
  const [summary, setSummary] = useState<LoadState<Summary>>({ data: emptySummary, loading: true, error: null });
  const [revenue, setRevenue] = useState<LoadState<RevenueByWeekday[]>>({ data: [], loading: true, error: null });
  const [duration, setDuration] = useState<LoadState<DurationByWeekday[]>>({ data: [], loading: true, error: null });
  const [zones, setZones] = useState<LoadState<TopZone[]>>({ data: [], loading: true, error: null });

  function handleRangeChange(value: DateRangePickerValue) {
    setRange(value);
    setSummary((state) => ({ ...state, loading: true, error: null }));
    setRevenue((state) => ({ ...state, loading: true, error: null }));
    setDuration((state) => ({ ...state, loading: true, error: null }));
    setZones((state) => ({ ...state, loading: true, error: null }));
  }

  useEffect(() => {
    if ((range.from && !range.to) || (!range.from && range.to)) return;

    const controller = new AbortController();
    const dates = range.from && range.to
      ? { startDate: formatDate(range.from), endDate: formatDate(range.to) }
      : {};

    // Plain useEffect keeps one shared filter state; FastAPI caches identical ranges.
    void fetchSummary(dates, controller.signal)
      .then((data) => setSummary({ data, loading: false, error: null }))
      .catch((error: Error) => {
        if (error.name !== "AbortError") setSummary({ data: emptySummary, loading: false, error: error.message });
      });
    void fetchRevenueByWeekday(dates, controller.signal)
      .then((data) => setRevenue({ data, loading: false, error: null }))
      .catch((error: Error) => {
        if (error.name !== "AbortError") setRevenue({ data: [], loading: false, error: error.message });
      });
    void fetchDurationByWeekday(dates, controller.signal)
      .then((data) => setDuration({ data, loading: false, error: null }))
      .catch((error: Error) => {
        if (error.name !== "AbortError") setDuration({ data: [], loading: false, error: error.message });
      });
    void fetchTopZones(dates, controller.signal)
      .then((data) => setZones({ data, loading: false, error: null }))
      .catch((error: Error) => {
        if (error.name !== "AbortError") setZones({ data: [], loading: false, error: error.message });
      });

    return () => controller.abort();
  }, [range.from, range.to]);

  return (
    <main className="min-h-[100dvh] bg-zinc-100 px-4 py-8 text-zinc-950 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-[1400px]">
        <header className="flex flex-col gap-6 border-b border-zinc-300 pb-8 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="font-mono text-xs font-semibold uppercase tracking-[0.16em] text-amber-700">
              BigQuery analytics
            </p>
            <h1 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
              NYC Taxi Pipeline
            </h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-600 sm:text-base">
              Revenue, duration, and pickup-zone performance from the validated trips table.
            </p>
          </div>
          <div className="w-full lg:w-[360px]">
            <label className="mb-2 block text-sm font-medium text-zinc-700">Pickup date range</label>
            <DateRangePicker
              value={range}
              onValueChange={handleRangeChange}
              enableSelect={false}
              enableClear
              weekStartsOn={1}
              color="amber"
              placeholder="All available dates"
              className="w-full"
            />
            <p className="mt-2 text-xs text-zinc-600">Select both dates to apply BigQuery partition pruning.</p>
          </div>
        </header>

        {summary.error ? (
          <div className="mt-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800" role="alert">
            Summary unavailable: {summary.error}
          </div>
        ) : null}

        <section className="mt-8 grid grid-cols-1 gap-4 md:grid-cols-3" aria-label="Trip summary">
          <StatCard label="Total trips" value={summary.data.total_trips.toLocaleString("en-US")} loading={summary.loading} />
          <StatCard label="Total revenue" value={formatCurrency(summary.data.total_revenue)} loading={summary.loading} />
          <StatCard label="Average fare" value={formatCurrency(summary.data.avg_fare)} loading={summary.loading} />
        </section>

        <section className="mt-6 grid grid-cols-1 gap-6 xl:grid-cols-2">
          <RevenueByWeekdayChart {...revenue} />
          <DurationByWeekdayChart {...duration} />
        </section>

        <section className="mt-6">
          <TopZonesTable {...zones} />
        </section>
      </div>
    </main>
  );
}
