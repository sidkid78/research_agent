# --- Stage 1: Build Stage ---
    FROM node:20-alpine AS build

    WORKDIR /app
    
    # Install dependencies
    COPY package.json package-lock.json ./
    RUN npm ci --legacy-peer-deps
    
    # Copy the rest of the source code
    COPY . .
    
    # Build the application
    # This will use the "output: 'standalone'"
    # feature from next.config.ts
    RUN npm run build
    
    # --- Stage 2: Production Stage ---
    FROM node:20-alpine AS production
    
    WORKDIR /app
    
    ENV NODE_ENV=production
    ENV NEXT_TELEMETRY_DISABLED=1
    
    # Create non-root user
    RUN addgroup --system --gid 1001 nodejs
    RUN adduser --system --uid 1001 nextjs
    
    # Copy the standalone output
    # This includes .next/standalone, .next/static, and public
    COPY --from=build --chown=nextjs:nodejs /app/.next/standalone ./
    COPY --from=build --chown=nextjs:nodejs /app/.next/static ./.next/static
    COPY --from=build --chown=nextjs:nodejs /app/public ./public
    
    # Switch to non-root user
    USER nextjs
    
    EXPOSE 3000
    
    ENV PORT=3000
    ENV HOSTNAME="0.0.0.0"
    
    # Health check
    HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
        CMD node -e "require('http').get('http://localhost:3000', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"
    
    # Start the server
    CMD ["node", "server.js"]