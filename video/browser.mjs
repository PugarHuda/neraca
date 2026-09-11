// The browser act, recorded by Playwright itself: a visitor at the public
// deployment types an address, reads the stamped ticket, opens the registry.
import { chromium } from "playwright";
import { mkdirSync, readdirSync, renameSync } from "node:fs";
import { fileURLToPath } from "node:url";

const BASE = "https://neraca-psi.vercel.app";
const BYPASS = process.env.VERCEL_BYPASS || "";
const dir = fileURLToPath(new URL("./clips/", import.meta.url));
mkdirSync(dir, { recursive: true });

const browser = await chromium.launch();
const ctx = await browser.newContext({
  viewport: { width: 1600, height: 900 },
  recordVideo: { dir, size: { width: 1600, height: 900 } },
  deviceScaleFactor: 1,
});
const page = await ctx.newPage();
const pause = (ms) => page.waitForTimeout(ms);

const entry = BYPASS
  ? `${BASE}/?x-vercel-protection-bypass=${BYPASS}&x-vercel-set-bypass-cookie=true`
  : `${BASE}/`;
await page.goto(entry, { waitUntil: "networkidle" });
await pause(2500);
await page.getByLabel("Who are you about to deal with?").click();
await page.keyboard.type("0x5FaCEbD66D78A69b400dC702049374B95745FBc5", { delay: 45 });
await pause(600);
await page.getByRole("button", { name: "Ask the tariff" }).click();
await page.waitForSelector(".answer");
await pause(4500);
await page.getByLabel("Who are you about to deal with?").fill("");
await page.keyboard.type("0x000000000000000000000000000000000000dEaD", { delay: 35 });
await page.keyboard.press("Enter");
await page.waitForSelector(".answer");
await pause(3000);
await page.getByRole("link", { name: "Registry", exact: true }).click();
await page.waitForSelector("#profiles");
await pause(2500);
await page.mouse.wheel(0, 500);
await pause(2500);
await page.mouse.wheel(0, 700);
await pause(3000);
await ctx.close();
await browser.close();

const webm = readdirSync(dir).find((f) => f.endsWith(".webm"));
renameSync(`${dir}${webm}`, `${dir}browser.webm`);
console.log("browser clip:", `${dir}browser.webm`);
