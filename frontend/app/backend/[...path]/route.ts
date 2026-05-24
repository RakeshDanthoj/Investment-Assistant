import { proxyToBackend } from "@/lib/api/proxyBackend";

type RouteContext = {
  params: { path: string[] };
};

async function handle(request: Request, { params }: RouteContext) {
  return proxyToBackend(request, params.path);
}

export const GET = handle;
export const POST = handle;
export const PUT = handle;
export const PATCH = handle;
export const DELETE = handle;
export const HEAD = handle;
export const OPTIONS = handle;
