import { clsx, type ClassValue } from 'clsx';
import { useEffect, useRef } from 'react';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
	return twMerge(clsx(inputs));
}

/**
 * Trigger a callback function at a specific target time. If the target time is in the past, the callback will be triggered immediately.
 * null targetTime will disable the timer.
 * @param callback The function to be called at the target time
 * @param targetTime The time at which to trigger the callback. If null, the timer is disabled.
 */
export function useAtTime(callback: () => void, targetTime: Date | null) {
	const savedCallback = useRef(callback);

	useEffect(() => {
		savedCallback.current = callback;
	}, [callback]);

	useEffect(() => {
		if (targetTime == null) return;
		const target = targetTime.getTime();
		const delay = target - Date.now();

		if (delay <= 0) {
			savedCallback.current();
			return;
		}

		const id = window.setTimeout(() => {
			savedCallback.current();
		}, delay);

		return () => window.clearTimeout(id);
	}, [targetTime]);
}
