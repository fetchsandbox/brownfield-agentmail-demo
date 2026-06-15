import Link from 'next/link';

export default function Home() {
  return (
    <main
      style={{
        maxWidth: 640,
        margin: '80px auto',
        padding: 24,
        fontFamily: 'system-ui, sans-serif',
      }}
    >
      <h1 style={{ fontSize: 32, marginBottom: 8 }}>Acme Orders</h1>
      <p style={{ color: '#666', marginBottom: 24, lineHeight: 1.5 }}>
        Customer support reply hub — every order gets its own reply
        inbox so the agent can route customer emails back to the right
        order. Clerk for auth, Postgres for orders, Resend for outbound.
      </p>
      <p style={{ color: '#888', marginBottom: 32, fontSize: 14, lineHeight: 1.5 }}>
        Per-customer inbox provisioning + inbound message handling
        is not yet wired — see README → &ldquo;What&rsquo;s NOT wired yet&rdquo;.
      </p>
      <Link
        href="/orders/new"
        style={{
          display: 'inline-block',
          padding: '12px 24px',
          background: '#5b45ff',
          color: 'white',
          borderRadius: 8,
          textDecoration: 'none',
          fontWeight: 600,
        }}
      >
        Place an order
      </Link>
    </main>
  );
}
