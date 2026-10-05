/**
 * RecruiterScoreCard — rule-based score advisor inspired by interviewstreet/hiring-agent.
 *
 * Patterned after ./SpotlightCard (same cursor-track light surface) but comes on
 * screen with a cinematic stagger-reveal of the per-rule rationale. Zag motion
 * vdrag inward, low-opacity on zero (unfinished rules), max 25 FPS per resource
 * discipline.
 *
 * API call to `/api/recruiter_score` is cached via Zustand so it only runs once
 * per session.
 *
 * Static props:
 *   className — tailwind classes atop the standard glassmorphism backdrop
 *   hero — if true, extra "bombshell" padding and a header text
 */
import React, { useEffect, useRef } from 'react';
import { motion, animate } from "framer-motion";
import { useAppStore } from "../store/useAppStore";
import toast from "react-hot-toast";
import BorderBeam from "./BorderBeam";





export default function RecruiterScoreCard({
  className = "",
  hero = false,
}: {
  className?: string;
  hero?: boolean;
}) {
  const { recruiterScore, fetchRecruiterScore } = useAppStore();
  const itemRefs = useRef<(HTMLDivElement | null)[]>([]);

  // Load once hook
  useEffect(() => {
    if (!recruiterScore.loaded && !recruiterScore.loading) {
      fetchRecruiterScore().catch(() => {
        if (hero) {
          toast.error("Unable to load score. Try refreshing?");
        }
      });
    }
  }, [recruiterScore.loaded, recruiterScore.loading, fetchRecruiterScore, hero]);

  // Animation hook
  useEffect(() => {
    if (recruiterScore.data && recruiterScore.loaded) {
      const staggerDelay = 0.07;
      const vz = 30;

      recruiterScore.data.rationale.forEach((_, idx) => {
        const el = itemRefs.current[idx];
        if (!el) return;

        // Fade/in + vdrag cheat code — 80ms motion-safe
        animate(el, { opacity: [0, 1], y: [vz, 0] }, {
          duration: 0.4,
          delay: hero ? idx * staggerDelay + 0.3 : 0,
          ease: [0.4, 0, 0, 1], // back-snap
        });
      });
    }
  }, [recruiterScore, hero]);

  if (recruiterScore.loading) {
    return (
      <div
        className={`glass-card-backdrop shadow-xl rounded-xl p-6 ${className}`}
      >
        <div className="text-center">
          <motion.div
            animate={{ opacity: [0.3, 0.6] }}
            transition={{ duration: 0.8, repeat: Infinity, ease: "easeInOut" }}
            className="text-lg text-indigo-200"
          >
            Scoring your resume...
          </motion.div>
        </div>
      </div>
    );
  }

  if (recruiterScore.error || !recruiterScore.data) {
    return null;
  }

  const report = recruiterScore.data;
  const MAX_DOTS = 4;

  /* Glassmorphism backdrop (mirrors SpotlightCard) */
  return (
    <div
      className={`glass-card-backdrop shadow-xl rounded-xl ${hero ? "md:p-8 p-6" : "p-6"} ${className}`}
      style={hero ? { position: 'relative', overflow: 'hidden' } : undefined}
    >
      {hero && (
        <>
          <BorderBeam color="#a5b4fc" duration={9} radius="0.75rem" />
          <div className="text-center mb-6">
            <h2 className="text-xl text-indigo-200 font-bold">Your Resume — Review Impact per Rule</h2>
            <motion.div
              className="text-sm text-indigo-400 mt-1"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5, duration: 0.5 }}
            >
              {report.inspirer}
            </motion.div>
          </div>
        </>
      )}

      <div className="space-y-3">
        {report.rationale.length ? (
          report.rationale.map((rule, idx) => {
            const sign = Math.sign(rule.delta);
            const bg = sign === 1
              ? "bg-emerald-500/10 border-emerald-500 text-emerald-100"
              : sign === -1
                ? "bg-rose-500/12 border-rose-500 text-rose-100"
                : "border-indigo-500/30";
            return (
              <motion.div
                key={`${rule.rule}-${idx}`}
                ref={(el) => {
                  itemRefs.current[idx] = el;
                }}
                initial={{ opacity: 0, y: 30 }}
                style={{ opacity: 0 }}
                className={`flex items-baseline gap-3 px-3 py-1 rounded-md relative overflow-hidden ${bg}`}
              >
                <div className="font-mono w-10 shrink-0 tabular-nums">
                  {rule.delta > 0 ? `+${rule.delta}` : rule.delta}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-pretty">
                    {rule.note}
                  </div>
                </div>
                <div className="badge absolute top-1 right-1 text-xs text-opacity-40">
                  {rule.category}
                </div>
              </motion.div>
            );
          })
        ) : (
          <div className="text-indigo-300 text-center">
            (no rules triggered)
          </div>
        )}
      </div>

      <motion.div
        className="flex justify-between mt-6 pt-4 border-t border-indigo-900/20 gap-4"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.7, duration: 0.3 }}
      >
        <div className="category-dot-col">
          {Object.entries(report.by_category).map(([cat, val]) => {
            const n = Math.min(MAX_DOTS, Math.ceil((val + 20) / 10));
            return (
              <div key={cat} className="dot-col-item">
                <div className="text-xs text-indigo-400 capitalize">{cat.replaceAll('_', ' ')}</div>
                <div className="dots">
                  {Array.from({ length: n }).map((_, i) => (
                    <span key={`dot-${cat}-${i}`} className="dot filled" />
                  ))}
                  {Array.from({ length: MAX_DOTS - n }).map((_, i) => (
                    <span key={`dot-unfilled-${cat}-${i}`} className="dot" />
                  ))}
                </div>
              </div>
            );
          })}
        </div>
        <div className="totals-box">
          <div className="bonus">
            <span className="dot filled bonus-color" /> bonus +{report.bonus}
          </div>
          <div className="deduction">
            <span className="dot filled deduction-color" /> deduction {report.deduction}
          </div>
          <div className="total font-mono text-xl">{report.total}</div>
        </div>
      </motion.div>
    </div>
  );
}


/* CSS that tailwind can't 🪄 */
const styles = String.raw`
.glass-card-backdrop {
  background: rgba(30, 30, 50, 0.3);
  backdrop-filter: blur(36px);
  -webkit-backdrop-filter: blur(36px);
  border: 1px solid rgba(120, 120, 170, 0.2);
}

.dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(75, 85, 99, 0.3);
  margin-right: 2px;
}
.dot.filled {
  background-color: #93c5fd; /* indigo-400 */
}
.dot.filled.bonus-color {
  background-color: #10b981; /* emerald-500 */
}
.dot.filled.deduction-color {
  background-color: #ef4444; /* rose-500 */
}
.dot-col-item {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.35rem;
}
.category-dot-col {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 0.85rem 1.25rem;
  flex: 1;
  min-width: 0;
}
.dots {
  display: inline-flex;
  flex-direction: row;
  gap: 0.25rem;
}
.totals-box {
  display: grid;
  grid-template-areas:
    "bonus"
    "deduction"
    "total";
}
.total {
  justify-self: end;
  grid-area: total;
}
`;

(function mountCSS() {
  if (typeof document !== "undefined" && !document.getElementById("__recruiter-score-css")) {
    const node = document.createElement("style");
    node.id = "__recruiter-score-css";
    node.type = "text/css";
    node.appendChild(document.createTextNode(styles));
    document.head.appendChild(node);
  }
})();