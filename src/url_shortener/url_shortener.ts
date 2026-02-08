import express from 'express';
import bodyParser from 'body-parser';
import crypto from 'crypto';
import { x86 } from 'murmurhash3js';


// In-memory storage for URLs
const URLS: { [key: string]: string } = {};

// Helper function to generate a short URL using bitwise hash
function generateShortUrlBitwise(longURL: string, baseURL: string): string {
    let hash = 0;
    for (let i = 0; i < longURL.length; i++) {
        const charCode = longURL.charCodeAt(i);
        hash = (hash << 5) - hash + charCode; // Combine shifting and addition
        hash = hash & hash; // Ensure 32-bit overflow
    }

    let base64urlHash = Math.abs(hash).toString(36);

    // Handle hash collision
    while (URLS[base64urlHash] && URLS[base64urlHash] !== longURL) {
        console.log(`[WARNING] Collision detected for bitwise hash: "${base64urlHash}" input longURL: "${longURL}" existing longURL: "${URLS[base64urlHash]}"`);
        hash++;
        base64urlHash = Math.abs(hash).toString(36);
    }

    URLS[base64urlHash] = longURL;
    return `${baseURL}/${base64urlHash}`;
}

// Helper function to generate a short URL using MD5 hash with base64url encoding
function generateShortUrlMD5(longURL: string, baseURL: string): string {
    let hash = crypto.createHash('md5').update(longURL).digest('base64url');

    // Handle hash collision
    while (URLS[hash] && URLS[hash] !== longURL) {
        console.log(`[WARNING] Collision detected for MD5 hash: "${hash}" input longURL: "${longURL}" existing longURL: "${URLS[hash]}"`);
        hash = crypto.createHash('md5').update(hash + '1').digest('base64url');
    }

    URLS[hash] = longURL;
    return `${baseURL}/${hash}`;
}

// Helper function to generate a short URL using SHA256 hash with base64url encoding
function generateShortUrlSHA256(longURL: string, baseURL: string): string {
    let hash = crypto.createHash('sha256').update(longURL).digest('base64url');

    // Handle hash collision
    while (URLS[hash] && URLS[hash] !== longURL) {
        console.log(`[WARNING] Collision detected for SHA256 hash: "${hash}" input longURL: "${longURL}" existing longURL: "${URLS[hash]}"`);
        hash = crypto.createHash('sha256').update(hash + '1').digest('base64url');
    }

    URLS[hash] = longURL;
    return `${baseURL}/${hash}`;
}

// Helper function to generate a short URL using MurmurHash hash with base64url encoding
function generateShortUrlMurmurBase64Url(longURL: string, baseURL: string): string {
    let hashInt: number = parseInt(x86.hash32(longURL), 10);
    let hash = Math.abs(Number(hashInt)).toString(36);

    // Handle hash collision
    while (URLS[hash] && URLS[hash] !== longURL) {
        console.log(`[WARNING] Collision detected for Murmur hash: "${hash}" input longURL: "${longURL}" existing longURL: "${URLS[hash]}"`);
        hashInt++;
        hash = Math.abs(Number(hashInt)).toString(36);
    }

    URLS[hash] = longURL;
    return `${baseURL}/${hash}`;
}

// Helper function to generate a short URL using MurmurHash hash with base64url encoding
function generateShortUrlMurmurInt(longURL: string, baseURL: string): string {
    let hash = x86.hash32(longURL).toString();

    // Handle hash collision
    while (URLS[hash] && URLS[hash] !== longURL) {
        console.log(`[WARNING] Collision detected for Murmur hash: "${hash}" input longURL: "${longURL}" existing longURL: "${URLS[hash]}"`);
        longURL += '1';
        hash = x86.hash32(longURL).toString();
    }

    URLS[hash] = longURL;
    return `${baseURL}/${hash}`;
}


// Function to create an Express app
function createApp(generator: (longURL: string, baseURL: string) => string) {
    const app = express();
    app.use(bodyParser.json());

    // POST endpoint to create a short URL
    app.post('/shorten', (req, res) => {
        const { longURL } = req.body;
        if (!longURL) {
            return res.status(400).send('longURL is required');
        }

        const baseURL = `http://localhost:${req.socket.localPort}`;
        const shortURL = generator(longURL, baseURL);
        res.json({ shortURL });
    });

    // GET endpoint to redirect to the long URL
    app.get('/:hash', (req, res) => {
        const { hash } = req.params;
        const longURL = URLS[hash];
        if (!longURL) {
            return res.status(404).send('URL not found');
        }
        res.redirect(longURL);
    });

    return { app };
}

export { createApp, generateShortUrlBitwise, generateShortUrlMD5, generateShortUrlSHA256,  generateShortUrlMurmurBase64Url, generateShortUrlMurmurInt };
