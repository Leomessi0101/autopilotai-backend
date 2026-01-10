const corsHeaders = {
	"Access-Control-Allow-Origin": "https://www.autopilotai.dev",
	"Access-Control-Allow-Methods": "POST, OPTIONS",
	"Access-Control-Allow-Headers": "Content-Type",
};

export default {
	async fetch(request, env) {
		// Handle CORS preflight
		if (request.method === "OPTIONS") {
			return new Response(null, {
				status: 204,
				headers: corsHeaders,
			});
		}

		if (request.method !== "POST") {
			return new Response("Method Not Allowed", {
				status: 405,
				headers: corsHeaders,
			});
		}

		const contentType = request.headers.get("content-type") || "";
		if (!contentType.includes("multipart/form-data")) {
			return new Response("Invalid content type", {
				status: 400,
				headers: corsHeaders,
			});
		}

		const formData = await request.formData();
		const file = formData.get("file");

		if (!file || typeof file === "string") {
			return new Response("Missing file", {
				status: 400,
				headers: corsHeaders,
			});
		}

		const extension = file.name.split(".").pop();
		const filename = `${crypto.randomUUID()}.${extension}`;

		await env.MEDIA_BUCKET.put(filename, file.stream(), {
			httpMetadata: {
				contentType: file.type,
			},
		});

		const publicUrl = `https://cdn.autopilotai.dev/${filename}`;

		return new Response(
			JSON.stringify({ url: publicUrl }),
			{
				headers: {
					...corsHeaders,
					"Content-Type": "application/json",
				},
			}
		);
	},
};
