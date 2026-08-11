/** React binding for {@link RegenerationScheduler}. */
import { useEffect, useMemo, useState } from 'react';

import {
  RegenerationScheduler,
  initialState,
  postGenerate,
  type RegenerationState,
} from './regeneration.ts';

export function useRegeneration(generator: string, debounceMs = 150) {
  const [state, setState] = useState<RegenerationState>(initialState);
  const scheduler = useMemo(
    () =>
      new RegenerationScheduler({
        generator,
        send: postGenerate,
        onState: setState,
        debounceMs,
      }),
    [generator, debounceMs],
  );
  useEffect(() => () => scheduler.dispose(), [scheduler]);
  return {
    state,
    request: (params: Record<string, unknown>, changed: string | null = null) =>
      scheduler.request(params, changed),
  };
}
