// Punto base de la API.
// Si cambias de puerto o IP, solo modificas aquí.
function getApiBase() {
    return "http://127.0.0.1:8000";
}

async function apiGet(url) {
    const res = await fetch(url);
    if (!res.ok) {
        const text = await res.text();
        throw new Error(text || res.statusText);
    }
    return res.json();
}

async function apiPost(url, payload) {
    const res = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
    });
    if (!res.ok) {
        const text = await res.text();
        throw new Error(text || res.statusText);
    }
    return res.json();
}
