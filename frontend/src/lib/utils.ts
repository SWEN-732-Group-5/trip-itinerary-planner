import { clsx, type ClassValue } from 'clsx';
import { useEffect, useRef } from 'react';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
	return twMerge(clsx(inputs));
}

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
