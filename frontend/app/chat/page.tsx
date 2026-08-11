"use client";

import {
  type CSSProperties,
  type FormEvent,
  type KeyboardEvent,
  type WheelEvent,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import ProtectedLayout from "@/components/ProtectedLayout";
import { apiFetch } from "@/lib/api";

import "./chat.css";


const CHATS_API_URL =
  "http://127.0.0.1:8000/api/chats/";


interface Chat {
  id: number;
  title: string;
  created_at?: string;
  updated_at?: string;
}


interface Message {
  id: number;
  role: "user" | "assistant";
  content: string;
  created_at?: string;
}


interface ApiErrorShape {
  detail?: string;
  [key: string]: unknown;
}


interface BeamGeometry {
  width: number;
  height: number;
  startX: number;
  startY: number;
  endX: number;
  endY: number;
  path: string;
}


function getErrorMessage(
  error: unknown
) {
  if (error instanceof Error) {
    return error.message;
  }

  return "Something went wrong.";
}


function extractApiError(
  data: unknown,
  fallback: string
) {
  if (
    !data
    || typeof data !== "object"
  ) {
    return fallback;
  }

  const object =
    data as ApiErrorShape;

  if (
    typeof object.detail
    === "string"
  ) {
    return object.detail;
  }

  const messages: string[] = [];

  function collect(
    value: unknown
  ) {
    if (
      typeof value === "string"
    ) {
      messages.push(value);
      return;
    }

    if (Array.isArray(value)) {
      value.forEach(collect);
      return;
    }

    if (
      value
      && typeof value === "object"
    ) {
      Object.values(value)
        .forEach(collect);
    }
  }

  collect(object);

  return messages[0] ?? fallback;
}


async function parseResponse(
  response: Response
) {
  if (response.status === 204) {
    return null;
  }

  const contentType =
    response.headers.get(
      "content-type"
    );

  if (
    contentType?.includes(
      "application/json"
    )
  ) {
    return response.json();
  }

  return null;
}


function makeTemporaryMessage(
  content: string
): Message {
  return {
    id: -Date.now(),
    role: "user",
    content,
  };
}


export default function ChatPage() {
  const [
    chats,
    setChats,
  ] = useState<Chat[]>([]);

  const [
    messages,
    setMessages,
  ] = useState<Message[]>([]);

  const [
    selectedChatId,
    setSelectedChatId,
  ] = useState<number | null>(
    null
  );

  const [
    message,
    setMessage,
  ] = useState("");

  const [
    newChatTitle,
    setNewChatTitle,
  ] = useState("");

  const [
    isLoadingChats,
    setIsLoadingChats,
  ] = useState(true);

  const [
    isLoadingMessages,
    setIsLoadingMessages,
  ] = useState(false);

  const [
    isSending,
    setIsSending,
  ] = useState(false);

  const [
    isCreatingChat,
    setIsCreatingChat,
  ] = useState(false);

  const [
    isCreateOpen,
    setIsCreateOpen,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState("");

  const [
    createError,
    setCreateError,
  ] = useState("");

  const [
    canScrollChatsLeft,
    setCanScrollChatsLeft,
  ] = useState(false);

  const [
    canScrollChatsRight,
    setCanScrollChatsRight,
  ] = useState(false);

  const [
    beamGeometry,
    setBeamGeometry,
  ] = useState<BeamGeometry | null>(
    null
  );


  const messageScrollerRef =
    useRef<HTMLDivElement | null>(
      null
    );

  const messagesEndRef =
    useRef<HTMLDivElement | null>(
      null
    );

  const textareaRef =
    useRef<HTMLTextAreaElement | null>(
      null
    );

  const chatStageRef =
    useRef<HTMLDivElement | null>(
      null
    );

  const chatPickerRef =
    useRef<HTMLDivElement | null>(
      null
    );

  const chatWindowRef =
    useRef<HTMLElement | null>(
      null
    );

  const chatCardRefs = useRef(
    new Map<
      number,
      HTMLButtonElement
    >()
  );

  const layoutFrameRef =
    useRef<number | null>(null);


  const selectedChat =
    useMemo(
      () => {
        if (
          selectedChatId === null
        ) {
          return null;
        }

        return (
          chats.find(
            (chat) =>
              chat.id
              === selectedChatId
          )
          ?? null
        );
      },
      [
        chats,
        selectedChatId,
      ]
    );


  const updateChatRailLayout =
    useCallback(() => {
      const rail =
        chatPickerRef.current;

      if (!rail) {
        setCanScrollChatsLeft(false);
        setCanScrollChatsRight(false);
        setBeamGeometry(null);
        return;
      }

      const maximumScroll = Math.max(
        0,
        rail.scrollWidth
        - rail.clientWidth
      );
      const canNavigate =
        !isLoadingChats
        && chats.length > 0;

      setCanScrollChatsLeft(
        canNavigate
        && rail.scrollLeft > 1
      );

      setCanScrollChatsRight(
        canNavigate
        && rail.scrollLeft
          < maximumScroll - 1
      );

      const stage =
        chatStageRef.current;
      const chatWindow =
        chatWindowRef.current;
      const activeCard =
        selectedChatId === null
          ? null
          : chatCardRefs.current.get(
              selectedChatId
            );

      if (
        !stage
        || !chatWindow
        || !activeCard
      ) {
        setBeamGeometry(null);
        return;
      }

      const stageRect =
        stage.getBoundingClientRect();
      const cardRect =
        activeCard.getBoundingClientRect();
      const windowRect =
        chatWindow.getBoundingClientRect();

      const startX =
        cardRect.left
        + cardRect.width / 2
        - stageRect.left;
      const startY =
        cardRect.bottom
        - stageRect.top;

      const windowCenterX =
        windowRect.left
        + windowRect.width / 2
        - stageRect.left;
      const horizontalPull = Math.max(
        -28,
        Math.min(
          28,
          (windowCenterX - startX)
          * 0.08
        )
      );
      const endX =
        startX + horizontalPull;
      const endY =
        windowRect.top
        - stageRect.top;
      const beamHeight =
        endY - startY;

      if (beamHeight < 4) {
        setBeamGeometry(null);
        return;
      }

      const lead = Math.min(
        10,
        beamHeight * 0.34
      );
      const path = [
        `M ${startX} ${startY}`,
        `L ${startX} ${startY + lead}`,
        `C ${startX} ${startY + beamHeight * 0.58}`,
        `${endX} ${endY - beamHeight * 0.28}`,
        `${endX} ${endY}`,
      ].join(" ");

      const nextGeometry = {
        width: stageRect.width,
        height: stageRect.height,
        startX,
        startY,
        endX,
        endY,
        path,
      };

      setBeamGeometry(
        (current) => {
          if (
            current
            && current.path === path
            && current.width
              === nextGeometry.width
            && current.height
              === nextGeometry.height
          ) {
            return current;
          }

          return nextGeometry;
        }
      );
    }, [
      chats.length,
      isLoadingChats,
      selectedChatId,
    ]);


  const scheduleChatRailLayout =
    useCallback(() => {
      if (
        layoutFrameRef.current
        !== null
      ) {
        return;
      }

      layoutFrameRef.current =
        window.requestAnimationFrame(
          () => {
            layoutFrameRef.current =
              null;
            updateChatRailLayout();
          }
        );
    }, [updateChatRailLayout]);


  const loadMessages =
    useCallback(
      async (
        chatId: number,
        showLoading = true
      ) => {
        if (showLoading) {
          setIsLoadingMessages(true);
        }

        setError("");

        try {
          const response =
            await apiFetch(
              `${CHATS_API_URL}${chatId}/messages/`
            );

          const data =
            await parseResponse(
              response
            );

          if (!response.ok) {
            throw new Error(
              extractApiError(
                data,
                "Could not load messages."
              )
            );
          }

          setMessages(
            Array.isArray(data)
              ? data
              : []
          );
        } catch (requestError) {
          setError(
            getErrorMessage(
              requestError
            )
          );
        } finally {
          setIsLoadingMessages(
            false
          );
        }
      },
      []
    );


  const loadChats =
    useCallback(
      async () => {
        setIsLoadingChats(true);
        setError("");

        try {
          const response =
            await apiFetch(
              CHATS_API_URL
            );

          const data =
            await parseResponse(
              response
            );

          if (!response.ok) {
            throw new Error(
              extractApiError(
                data,
                "Could not load chats."
              )
            );
          }

          const loadedChats: Chat[] =
            Array.isArray(data)
              ? data
              : [];

          setChats(
            loadedChats
          );

          if (
            loadedChats.length === 0
          ) {
            setSelectedChatId(null);
            setMessages([]);
            return;
          }

          setSelectedChatId(
            (currentId) => {
              const exists =
                loadedChats.some(
                  (chat) =>
                    chat.id
                    === currentId
                );

              if (
                currentId !== null
                && exists
              ) {
                return currentId;
              }

              return loadedChats[0].id;
            }
          );
        } catch (requestError) {
          setError(
            getErrorMessage(
              requestError
            )
          );
        } finally {
          setIsLoadingChats(
            false
          );
        }
      },
      []
    );


  useEffect(() => {
    const timeoutId =
      window.setTimeout(
        () => {
          void loadChats();
        },
        0
      );

    return () => {
      window.clearTimeout(
        timeoutId
      );
    };
  }, [loadChats]);


  useEffect(() => {
    if (
      selectedChatId === null
    ) {
      return;
    }

    const timeoutId =
      window.setTimeout(
        () => {
          setMessages([]);

          void loadMessages(
            selectedChatId
          );
        },
        0
      );

    return () => {
      window.clearTimeout(
        timeoutId
      );
    };
  }, [
    selectedChatId,
    loadMessages,
  ]);


  useEffect(() => {
    if (
      isLoadingChats
      || selectedChatId === null
    ) {
      scheduleChatRailLayout();
      return;
    }

    const rail =
      chatPickerRef.current;
    const activeCard =
      chatCardRefs.current.get(
        selectedChatId
      );

    if (!rail || !activeCard) {
      scheduleChatRailLayout();
      return;
    }

    const railRect =
      rail.getBoundingClientRect();
    const cardRect =
      activeCard.getBoundingClientRect();
    const cardLeftInRail =
      cardRect.left
      - railRect.left
      + rail.scrollLeft;
    const targetLeft =
      cardLeftInRail
      - (
        rail.clientWidth
        - cardRect.width
      ) / 2;

    rail.scrollTo({
      left: Math.max(0, targetLeft),
      behavior: "smooth",
    });

    scheduleChatRailLayout();
  }, [
    chats,
    isLoadingChats,
    selectedChatId,
    scheduleChatRailLayout,
  ]);


  useEffect(() => {
    const stage =
      chatStageRef.current;
    const rail =
      chatPickerRef.current;
    const chatWindow =
      chatWindowRef.current;

    const resizeObserver =
      typeof ResizeObserver
      === "undefined"
        ? null
        : new ResizeObserver(
            scheduleChatRailLayout
          );

    if (stage) {
      resizeObserver?.observe(stage);
    }

    if (rail) {
      resizeObserver?.observe(rail);
    }

    if (chatWindow) {
      resizeObserver?.observe(
        chatWindow
      );
    }

    window.addEventListener(
      "resize",
      scheduleChatRailLayout
    );

    scheduleChatRailLayout();

    return () => {
      resizeObserver?.disconnect();

      window.removeEventListener(
        "resize",
        scheduleChatRailLayout
      );

      if (
        layoutFrameRef.current
        !== null
      ) {
        window.cancelAnimationFrame(
          layoutFrameRef.current
        );
        layoutFrameRef.current = null;
      }
    };
  }, [
    chats.length,
    isLoadingChats,
    selectedChatId,
    scheduleChatRailLayout,
  ]);


  useEffect(() => {
    if (
      isLoadingMessages
    ) {
      return;
    }

    window.setTimeout(
      () => {
        const scroller =
          messageScrollerRef.current;

        if (!scroller) {
          return;
        }

        scroller.scrollTop =
          scroller.scrollHeight;
      },
      0
    );
  }, [
    messages,
    isLoadingMessages,
    isSending,
  ]);


  useEffect(() => {
    function handleEscape(
      event: globalThis.KeyboardEvent
    ) {
      if (
        event.key === "Escape"
        && isCreateOpen
        && !isCreatingChat
      ) {
        setIsCreateOpen(false);
        setNewChatTitle("");
        setCreateError("");
      }
    }

    window.addEventListener(
      "keydown",
      handleEscape
    );

    return () => {
      window.removeEventListener(
        "keydown",
        handleEscape
      );
    };
  }, [
    isCreateOpen,
    isCreatingChat,
  ]);


  function openCreateModal() {
    setNewChatTitle("");
    setCreateError("");
    setIsCreateOpen(true);
  }


  function closeCreateModal() {
    if (isCreatingChat) {
      return;
    }

    setIsCreateOpen(false);
    setNewChatTitle("");
    setCreateError("");
  }


  async function createChat(
    event: FormEvent
  ) {
    event.preventDefault();

    const cleanTitle =
      newChatTitle.trim();

    if (!cleanTitle) {
      setCreateError(
        "Name the chat first."
      );
      return;
    }

    setIsCreatingChat(true);
    setCreateError("");

    try {
      const response =
        await apiFetch(
          CHATS_API_URL,
          {
            method: "POST",
            headers: {
              "Content-Type":
                "application/json",
            },
            body: JSON.stringify({
              title: cleanTitle,
            }),
          }
        );

      const data =
        await parseResponse(
          response
        );

      if (!response.ok) {
        throw new Error(
          extractApiError(
            data,
            "Could not create the chat."
          )
        );
      }

      const createdChat =
        data as Chat;

      setChats(
        (current) => [
          createdChat,
          ...current.filter(
            (chat) =>
              chat.id
              !== createdChat.id
          ),
        ]
      );

      setMessages([]);
      setSelectedChatId(
        createdChat.id
      );

      setNewChatTitle("");
      setIsCreateOpen(false);
    } catch (requestError) {
      setCreateError(
        getErrorMessage(
          requestError
        )
      );
    } finally {
      setIsCreatingChat(false);
    }
  }


  function selectChat(
    chatId: number
  ) {
    if (
      chatId === selectedChatId
    ) {
      return;
    }

    setSelectedChatId(
      chatId
    );
  }


  async function sendMessage(
    event?: FormEvent
  ) {
    event?.preventDefault();

    if (
      selectedChatId === null
      || isSending
    ) {
      return;
    }

    const cleanMessage =
      message.trim();

    if (!cleanMessage) {
      return;
    }

    const chatId =
      selectedChatId;

    const optimisticMessage =
      makeTemporaryMessage(
        cleanMessage
      );

    setMessage("");
    setError("");
    setIsSending(true);

    setMessages(
      (current) => [
        ...current,
        optimisticMessage,
      ]
    );

    try {
      const response =
        await apiFetch(
          `${CHATS_API_URL}${chatId}/messages/`,
          {
            method: "POST",
            headers: {
              "Content-Type":
                "application/json",
            },
            body: JSON.stringify({
              content: cleanMessage,
            }),
          }
        );

      const data =
        await parseResponse(
          response
        );

      if (!response.ok) {
        throw new Error(
          extractApiError(
            data,
            "Could not send the message."
          )
        );
      }

      await loadMessages(
        chatId,
        false
      );

      const chatsResponse =
        await apiFetch(
          CHATS_API_URL
        );

      const chatsData =
        await parseResponse(
          chatsResponse
        );

      if (
        chatsResponse.ok
        && Array.isArray(
          chatsData
        )
      ) {
        setChats(
          chatsData
        );
      }
    } catch (requestError) {
      setMessages(
        (current) =>
          current.filter(
            (item) =>
              item.id
              !== optimisticMessage.id
          )
      );

      setMessage(
        cleanMessage
      );

      setError(
        getErrorMessage(
          requestError
        )
      );
    } finally {
      setIsSending(false);

      window.setTimeout(
        () => {
          textareaRef.current
            ?.focus();
        },
        0
      );
    }
  }


  function handleMessageKeyDown(
    event:
      KeyboardEvent<HTMLTextAreaElement>
  ) {
    if (
      event.key !== "Enter"
      || event.shiftKey
    ) {
      return;
    }

    event.preventDefault();

    if (
      !isSending
      && message.trim()
    ) {
      void sendMessage();
    }
  }


  function scrollChatRail(
    direction: -1 | 1
  ) {
    const rail =
      chatPickerRef.current;

    if (!rail) {
      return;
    }

    const firstCard =
      chatCardRefs.current
        .values()
        .next()
        .value as
          | HTMLButtonElement
          | undefined;
    const cardStep =
      (firstCard?.offsetWidth ?? 158)
      + 12;

    rail.scrollBy({
      left:
        direction
        * cardStep
        * 2.5,
      behavior: "smooth",
    });
  }


  function handleChatRailWheel(
    event: WheelEvent<HTMLDivElement>
  ) {
    const rail = event.currentTarget;
    const maximumScroll =
      rail.scrollWidth
      - rail.clientWidth;

    if (
      maximumScroll <= 1
      || Math.abs(event.deltaY)
        <= Math.abs(event.deltaX)
      || event.deltaY === 0
    ) {
      return;
    }

    const canMove =
      event.deltaY > 0
        ? rail.scrollLeft
          < maximumScroll - 1
        : rail.scrollLeft > 1;

    if (!canMove) {
      return;
    }

    event.preventDefault();
    rail.scrollLeft += event.deltaY;
  }


  return (
    <ProtectedLayout>
      <main className="chat-page">
        <section className="chat-shell">
          <header className="chat-page-header">
            <div className="chat-page-heading">
              <span className="chat-heading-dot" />

              <h1>
                AI Chats
              </h1>
            </div>
          </header>


          {error && (
            <div
              className="chat-error"
              role="alert"
            >
              <span>
                {error}
              </span>

              <button
                type="button"
                onClick={() =>
                  setError("")
                }
                aria-label="Dismiss error"
              >
                ×
              </button>
            </div>
          )}


          <div
            ref={chatStageRef}
            className="chat-stage"
            style={{
              "--beam-end-x":
                beamGeometry
                  ? `${beamGeometry.endX}px`
                  : "-20px",
            } as CSSProperties}
          >
            <section className="chat-picker">
              <div className="chat-picker-rail">
                <button
                  type="button"
                  className={[
                    "chat-picker-arrow",
                    canScrollChatsLeft
                      ? "is-visible"
                      : "",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                  onClick={() =>
                    scrollChatRail(-1)
                  }
                  aria-label="Scroll chats left"
                  aria-hidden={
                    !canScrollChatsLeft
                  }
                  tabIndex={
                    canScrollChatsLeft
                      ? 0
                      : -1
                  }
                >
                  ‹
                </button>

                <div
                  ref={chatPickerRef}
                  className="chat-picker-list"
                  onScroll={
                    scheduleChatRailLayout
                  }
                  onWheel={
                    handleChatRailWheel
                  }
                  aria-label="Chats"
                >
                  {isLoadingChats ? (
                    <div className="chat-picker-loading">
                      <span />
                      <span />
                      <span />
                    </div>
                  ) : chats.map(
                    (chat) => (
                      <button
                        key={chat.id}
                        ref={(element) => {
                          if (element) {
                            chatCardRefs
                              .current
                              .set(
                                chat.id,
                                element
                              );
                          } else {
                            chatCardRefs
                              .current
                              .delete(
                                chat.id
                              );
                          }
                        }}
                        type="button"
                        className={[
                          "chat-picker-item",
                          selectedChatId
                          === chat.id
                            ? "is-active"
                            : "",
                        ]
                          .filter(Boolean)
                          .join(" ")}
                        onClick={() =>
                          selectChat(
                            chat.id
                          )
                        }
                      >
                        <strong>
                          {chat.title}
                        </strong>
                      </button>
                    )
                  )}
                </div>

                <button
                  type="button"
                  className={[
                    "chat-picker-arrow",
                    canScrollChatsRight
                      ? "is-visible"
                      : "",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                  onClick={() =>
                    scrollChatRail(1)
                  }
                  aria-label="Scroll chats right"
                  aria-hidden={
                    !canScrollChatsRight
                  }
                  tabIndex={
                    canScrollChatsRight
                      ? 0
                      : -1
                  }
                >
                  ›
                </button>
              </div>

              <button
                type="button"
                className="chat-picker-add"
                onClick={
                  openCreateModal
                }
                aria-label="Create new chat"
              >
                +
              </button>
            </section>


            {beamGeometry && (
              <svg
                className="chat-active-beam"
                viewBox={
                  `0 0 ${beamGeometry.width} ${beamGeometry.height}`
                }
                preserveAspectRatio="none"
                aria-hidden="true"
              >
                <defs>
                  <linearGradient
                    id="chat-beam-stroke"
                    x1="0"
                    y1="0"
                    x2="0"
                    y2="1"
                  >
                    <stop
                      offset="0%"
                      stopColor="rgba(184, 163, 255, 0.5)"
                    />
                    <stop
                      offset="55%"
                      stopColor="rgba(152, 124, 242, 0.3)"
                    />
                    <stop
                      offset="100%"
                      stopColor="rgba(152, 124, 242, 0.18)"
                    />
                  </linearGradient>
                </defs>

                <path
                  className="chat-active-beam-glow"
                  d={beamGeometry.path}
                />

                <path
                  className="chat-active-beam-line"
                  d={beamGeometry.path}
                />

              </svg>
            )}


          {selectedChat === null ? (
            <section className="chat-empty-page">
              <h2>
                Start a new chat.
              </h2>

              <button
                type="button"
                onClick={
                  openCreateModal
                }
              >
                + New chat
              </button>
            </section>
          ) : (
            <section
              ref={chatWindowRef}
              className="chat-window"
            >
              <header className="chat-window-header">
                <h2>
                  {selectedChat.title}
                </h2>
              </header>


              <div
                ref={
                  messageScrollerRef
                }
                className="chat-window-messages"
              >
                {isLoadingMessages ? (
                  <div className="chat-messages-loading">
                    <span />
                  </div>
                ) : messages.length
                === 0 ? (
                  <div className="chat-empty-conversation">
                    <h3>
                      {selectedChat.title}
                    </h3>

                    <p>
                      Start the conversation.
                    </p>
                  </div>
                ) : (
                  <div className="chat-message-stream">
                    {messages.map(
                      (
                        item
                      ) => (
                        <article
                          key={
                            item.id
                          }
                          className={[
                            "chat-message",
                            item.role
                            === "user"
                              ? "is-user"
                              : "is-assistant",
                            item.id < 0
                              ? "is-pending"
                              : "",
                          ]
                            .filter(Boolean)
                            .join(" ")}
                        >
                          <div className="chat-message-meta">
                            {item.role
                            === "user"
                              ? "You"
                              : "PROJECT"}
                          </div>

                          <div className="chat-message-content">
                            {item.content
                              .split("\n")
                              .map(
                                (
                                  paragraph,
                                  index
                                ) => (
                                  <p
                                    key={
                                      index
                                    }
                                  >
                                    {paragraph
                                    || "\u00A0"}
                                  </p>
                                )
                              )}
                          </div>
                        </article>
                      )
                    )}


                    {isSending && (
                      <article className="chat-message is-assistant is-thinking">
                        <div className="chat-message-meta">
                          PROJECT
                        </div>

                        <div className="chat-thinking">
                          <span />
                          <span />
                          <span />
                        </div>
                      </article>
                    )}


                    <div
                      ref={
                        messagesEndRef
                      }
                    />
                  </div>
                )}
              </div>


              <div className="chat-window-composer">
                <form
                  className="chat-composer"
                  onSubmit={
                    sendMessage
                  }
                >
                  <textarea
                    ref={
                      textareaRef
                    }
                    value={message}
                    onChange={(
                      event
                    ) =>
                      setMessage(
                        event
                          .target
                          .value
                      )
                    }
                    onKeyDown={
                      handleMessageKeyDown
                    }
                    placeholder={`Message ${selectedChat.title}`}
                    rows={1}
                    disabled={
                      isSending
                    }
                  />

                  <button
                    type="submit"
                    className="chat-send-button"
                    disabled={
                      isSending
                      || !message.trim()
                    }
                    aria-label="Send message"
                  >
                    ↑
                  </button>
                </form>
              </div>
            </section>
          )}
          </div>
        </section>


        {isCreateOpen && (
          <div
            className="chat-modal-backdrop"
            role="presentation"
            onMouseDown={(
              event
            ) => {
              if (
                event.target
                === event.currentTarget
              ) {
                closeCreateModal();
              }
            }}
          >
            <section
              className="chat-modal"
              role="dialog"
              aria-modal="true"
              aria-labelledby="new-chat-title"
            >
              <button
                type="button"
                className="chat-modal-close"
                onClick={
                  closeCreateModal
                }
                aria-label="Close"
              >
                ×
              </button>

              <header className="chat-modal-header">
                <span>
                  New chat
                </span>

                <h2 id="new-chat-title">
                  What is this chat about?
                </h2>
              </header>


              <form
                className="chat-create-form"
                onSubmit={
                  createChat
                }
              >
                <label>
                  <span>
                    Name
                  </span>

                  <input
                    type="text"
                    value={
                      newChatTitle
                    }
                    onChange={(
                      event
                    ) =>
                      setNewChatTitle(
                        event
                          .target
                          .value
                      )
                    }
                    placeholder="English B2"
                    maxLength={255}
                    autoFocus
                  />
                </label>


                {createError && (
                  <div
                    className="chat-create-error"
                    role="alert"
                  >
                    {createError}
                  </div>
                )}


                <footer className="chat-modal-actions">
                  <button
                    type="button"
                    onClick={
                      closeCreateModal
                    }
                  >
                    Cancel
                  </button>

                  <button
                    type="submit"
                    disabled={
                      isCreatingChat
                      || !newChatTitle.trim()
                    }
                  >
                    {isCreatingChat
                      ? "Creating…"
                      : "Create"}
                  </button>
                </footer>
              </form>
            </section>
          </div>
        )}
      </main>
    </ProtectedLayout>
  );
}
