"use client";

import { FormEvent, useEffect, useState } from "react";

import { apiFetch } from "@/lib/api";
import ProtectedLayout from "@/components/ProtectedLayout";

interface Chat {
  id: number;
  title: string;
}

interface Message {
  id: number;
  role: string;
  content: string;
}

export default function ChatPage() {
  const [chats, setChats] = useState<Chat[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [selectedChat, setSelectedChat] =
    useState<number | null>(null);

  const [title, setTitle] = useState("");
  const [message, setMessage] = useState("");

  const [isLoading, setIsLoading] =
    useState(false);

  async function loadChats() {
    const response = await apiFetch(
      "http://127.0.0.1:8000/api/chats/"
    );

    const data = await response.json();

    if (Array.isArray(data)) {
      setChats(data);
    }
  }

  async function loadMessages(
    chatId: number
  ) {
    const response = await apiFetch(
      `http://127.0.0.1:8000/api/chats/${chatId}/messages/`
    );

    const data = await response.json();

    if (Array.isArray(data)) {
      setMessages(data);
    }

    setSelectedChat(chatId);
  }

  useEffect(() => {
    loadChats();
  }, []);

  async function createChat() {
    if (!title.trim()) {
      return;
    }

    const response = await apiFetch(
      "http://127.0.0.1:8000/api/chats/",
      {
        method: "POST",
        headers: {
          "Content-Type":
            "application/json",
        },
        body: JSON.stringify({
          title,
        }),
      }
    );

    if (response.ok) {
      setTitle("");

      await loadChats();
    }
  }

  async function sendMessage(
    event: FormEvent
  ) {
    event.preventDefault();

    if (
      !selectedChat ||
      !message.trim() ||
      isLoading
    ) {
      return;
    }

    setIsLoading(true);

    try {
      const response = await apiFetch(
        `http://127.0.0.1:8000/api/chats/${selectedChat}/messages/`,
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/json",
          },
          body: JSON.stringify({
            content: message,
          }),
        }
      );

      if (response.ok) {
        setMessage("");

        await loadMessages(
          selectedChat
        );
      }
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <ProtectedLayout>
      <main className="min-h-screen p-8">
        <h1 className="text-4xl font-bold mb-6">
          AI Chat
        </h1>

        <div className="grid grid-cols-4 gap-6">
          <div className="border rounded p-4">
            <input
              type="text"
              placeholder="New chat"
              value={title}
              onChange={(e) =>
                setTitle(e.target.value)
              }
              className="w-full border rounded p-2 mb-3"
            />

            <button
              onClick={createChat}
              className="w-full border rounded p-2 mb-4"
            >
              Create Chat
            </button>

            <div className="space-y-2">
              {chats.map((chat) => (
                <button
                  key={chat.id}
                  onClick={() =>
                    loadMessages(chat.id)
                  }
                  className="w-full border rounded p-2 text-left"
                >
                  {chat.title}
                </button>
              ))}
            </div>
          </div>

          <div className="col-span-3 border rounded p-4 flex flex-col">
            {selectedChat === null ? (
              <p>Select chat</p>
            ) : (
              <>
                <div className="flex-1 space-y-4 mb-6">
                  {messages.map(
                    (message) => (
                      <div
                        key={message.id}
                        className="border rounded p-3"
                      >
                        <strong>
                          {message.role}
                        </strong>

                        <p className="mt-2">
                          {message.content}
                        </p>
                      </div>
                    )
                  )}
                </div>

                <form
                  onSubmit={sendMessage}
                  className="flex gap-2"
                >
                  <input
                    type="text"
                    value={message}
                    onChange={(e) =>
                      setMessage(
                        e.target.value
                      )
                    }
                    placeholder="Message..."
                    className="flex-1 border rounded p-3"
                  />

                  <button
                    type="submit"
                    disabled={isLoading}
                    className="border rounded px-4"
                  >
                    {isLoading
                      ? "Thinking..."
                      : "Send"}
                  </button>
                </form>
              </>
            )}
          </div>
        </div>
      </main>
    </ProtectedLayout>
  );
}