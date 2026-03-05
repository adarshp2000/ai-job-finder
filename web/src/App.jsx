import { useEffect, useState } from "react";

const API = "http://127.0.0.1:8000";

function App() {
  const [jobs, setJobs] = useState([]);
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(false);

  async function fetchJobs() {
    setLoading(true);

    let url = `${API}/jobs?limit=50`;

    if (q) {
      url += `&q=${encodeURIComponent(q)}`;
    }

    const res = await fetch(url);
    const data = await res.json();

    setJobs(data);
    setLoading(false);
  }

  useEffect(() => {
    fetchJobs();
  }, []);

  return (
    <div style={{ maxWidth: 900, margin: "40px auto", fontFamily: "Arial" }}>
      <h1>AI Job Finder</h1>

      <div style={{ marginBottom: 20 }}>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search jobs..."
          style={{ padding: 8, width: 300 }}
        />

        <button
          onClick={fetchJobs}
          style={{ marginLeft: 10, padding: "8px 12px" }}
        >
          Search
        </button>
      </div>

      {loading && <p>Loading...</p>}

      {jobs.map((job) => (
        <div
          key={job.id}
          style={{
            border: "1px solid #ddd",
            padding: 15,
            marginBottom: 10,
            borderRadius: 6,
          }}
        >
          <h3>{job.title}</h3>

          <p>
            <b>{job.company}</b> — {job.location}
          </p>

          <a href={job.url} target="_blank">
            View Job
          </a>
        </div>
      ))}
    </div>
  );
}

export default App;