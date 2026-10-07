import { env } from "@/lib/env";

import { apiSimulatorSource } from "./api-source";
import { mockSimulatorSource } from "./mock-source";
import type { SimulatorDataSource } from "./types";

/** Runtime-selected source; UI and hooks remain source-agnostic. */
export const simulatorSource: SimulatorDataSource =
  env.NEXT_PUBLIC_SIMULATOR_SOURCE === "api"
    ? apiSimulatorSource
    : mockSimulatorSource;

export * from "./message-ordering";
export type * from "./types";
