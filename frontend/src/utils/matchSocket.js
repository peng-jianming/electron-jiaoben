import { io } from 'socket.io-client';

let matchSocket = null;
let initPromise = null;

export function initMatchSocket() {
  if (matchSocket) return Promise.resolve(matchSocket);
  if (initPromise) return initPromise;

  initPromise = new Promise((resolve) => {
    matchSocket = io('ws://localhost:7075');
    matchSocket.once('connect', () => {
      resolve(matchSocket);
    });
  });

  return initPromise;
}

export function getMatchSocket() {
  return matchSocket;
}

