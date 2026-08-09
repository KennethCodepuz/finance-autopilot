export async function getPendingApprovals(backendUrl?: string) {
    try {
        const baseUrl = backendUrl || process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
        const response = await fetch(`${baseUrl}/api/approvals/pending-approvals`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error("Error fetching pending approvals:", error);
        return [];
    }
}