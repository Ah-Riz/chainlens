"use client";

import { ConnectionProvider, WalletProvider } from "@solana/wallet-adapter-react";
import { WalletModalProvider } from "@solana/wallet-adapter-react-ui";
import { PhantomWalletAdapter } from "@solana/wallet-adapter-phantom";
import { SolflareWalletAdapter } from "@solana/wallet-adapter-solflare";
import { useMemo, type ComponentType, type ReactNode } from "react";

import "@solana/wallet-adapter-react-ui/styles.css";

type Kids = { children?: ReactNode };

const Conn = ConnectionProvider as ComponentType<{ endpoint: string } & Kids>;
const Wall = WalletProvider as ComponentType<{ wallets: unknown[]; autoConnect?: boolean } & Kids>;
const Modal = WalletModalProvider as ComponentType<Kids>;

export function Providers({ children }: { children: ReactNode }) {
  const endpoint = "https://api.mainnet-beta.solana.com";
  const wallets = useMemo(() => [new PhantomWalletAdapter(), new SolflareWalletAdapter()], []);

  return (
    <Conn endpoint={endpoint}>
      <Wall wallets={wallets} autoConnect>
        <Modal>{children}</Modal>
      </Wall>
    </Conn>
  );
}
