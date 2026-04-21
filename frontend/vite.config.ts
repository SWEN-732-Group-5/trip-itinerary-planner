import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { defineConfig, loadEnv } from 'vite';

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
	const env = loadEnv(mode, process.cwd(), '');
	const apiProxyTarget = env.VITE_API_PROXY_TARGET ?? 'http://localhost:8000';

	return {
		plugins: [react(), tailwindcss()],
		resolve: {
			alias: {
				'@': path.resolve(__dirname, './src'),
			},
		},
		server: {
			host: '0.0.0.0',
			proxy: {
				'/api': {
					target: apiProxyTarget,
					changeOrigin: true,
					secure: false,
				},
			},
		},
	};
});
