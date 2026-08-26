import ChatWidget from "@/components/chat/ChatWidget";

// Page vitrine publique du restaurant, avec le widget de chat client
export default function HomePage() {
  return (
    <main className="min-h-screen flex flex-col">
      <section className="p-6 text-center">
        <h1 className="text-2xl font-bold text-primary">
          Reservez votre table
        </h1>
        <p className="text-gray-600 mt-2">
          Discutez avec notre assistant pour reserver en quelques secondes.
        </p>
      </section>

      <ChatWidget />
    </main>
  );
}
