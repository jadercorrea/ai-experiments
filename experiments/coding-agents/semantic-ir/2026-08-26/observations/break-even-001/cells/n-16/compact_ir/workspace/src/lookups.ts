export type User = Readonly<{ id: string; name: string }>;
export type Result<T, E> = { ok: T } | { error: E };
export type SemanticCapabilities = Readonly<{
  users: Readonly<{ getById(id: string): User | undefined }>;
}>;

export function lookupUser01(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:n0001 */ (() => {
    const trimmed: string = /* ir:node:n0002 */ (/* ir:node:n0003 */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:n0004 */ (/* ir:node:n0005 */ (/* ir:node:n0006 */ trimmed).length === 0)
      ? (/* ir:node:n0007 */ { error: /* ir:node:n0008 */ "invalid_user_id" })
      : (/* ir:node:n0009 */ (() => {
          const __semantic_ir_option_1 = /* ir:node:n0010 */ capabilities.users.getById(/* ir:node:n0011 */ trimmed);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:n0012 */ { error: /* ir:node:n0013 */ "not_found" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:n0014 */ { ok: /* ir:node:n0015 */ user };
        })());
  })();
}

export function lookupUser02(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:n0001 */ (() => {
    const trimmed: string = /* ir:node:n0002 */ (/* ir:node:n0003 */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:n0004 */ (/* ir:node:n0005 */ (/* ir:node:n0006 */ trimmed).length === 0)
      ? (/* ir:node:n0007 */ { error: /* ir:node:n0008 */ "invalid_user_id" })
      : (/* ir:node:n0009 */ (() => {
          const __semantic_ir_option_1 = /* ir:node:n0010 */ capabilities.users.getById(/* ir:node:n0011 */ trimmed);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:n0012 */ { error: /* ir:node:n0013 */ "not_found" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:n0014 */ { ok: /* ir:node:n0015 */ user };
        })());
  })();
}

export function lookupUser03(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:n0001 */ (() => {
    const trimmed: string = /* ir:node:n0002 */ (/* ir:node:n0003 */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:n0004 */ (/* ir:node:n0005 */ (/* ir:node:n0006 */ trimmed).length === 0)
      ? (/* ir:node:n0007 */ { error: /* ir:node:n0008 */ "invalid_user_id" })
      : (/* ir:node:n0009 */ (() => {
          const __semantic_ir_option_1 = /* ir:node:n0010 */ capabilities.users.getById(/* ir:node:n0011 */ trimmed);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:n0012 */ { error: /* ir:node:n0013 */ "not_found" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:n0014 */ { ok: /* ir:node:n0015 */ user };
        })());
  })();
}

export function lookupUser04(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:n0001 */ (() => {
    const trimmed: string = /* ir:node:n0002 */ (/* ir:node:n0003 */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:n0004 */ (/* ir:node:n0005 */ (/* ir:node:n0006 */ trimmed).length === 0)
      ? (/* ir:node:n0007 */ { error: /* ir:node:n0008 */ "invalid_user_id" })
      : (/* ir:node:n0009 */ (() => {
          const __semantic_ir_option_1 = /* ir:node:n0010 */ capabilities.users.getById(/* ir:node:n0011 */ trimmed);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:n0012 */ { error: /* ir:node:n0013 */ "not_found" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:n0014 */ { ok: /* ir:node:n0015 */ user };
        })());
  })();
}

export function lookupUser05(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:n0001 */ (() => {
    const trimmed: string = /* ir:node:n0002 */ (/* ir:node:n0003 */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:n0004 */ (/* ir:node:n0005 */ (/* ir:node:n0006 */ trimmed).length === 0)
      ? (/* ir:node:n0007 */ { error: /* ir:node:n0008 */ "invalid_user_id" })
      : (/* ir:node:n0009 */ (() => {
          const __semantic_ir_option_1 = /* ir:node:n0010 */ capabilities.users.getById(/* ir:node:n0011 */ trimmed);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:n0012 */ { error: /* ir:node:n0013 */ "not_found" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:n0014 */ { ok: /* ir:node:n0015 */ user };
        })());
  })();
}

export function lookupUser06(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:n0001 */ (() => {
    const trimmed: string = /* ir:node:n0002 */ (/* ir:node:n0003 */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:n0004 */ (/* ir:node:n0005 */ (/* ir:node:n0006 */ trimmed).length === 0)
      ? (/* ir:node:n0007 */ { error: /* ir:node:n0008 */ "invalid_user_id" })
      : (/* ir:node:n0009 */ (() => {
          const __semantic_ir_option_1 = /* ir:node:n0010 */ capabilities.users.getById(/* ir:node:n0011 */ trimmed);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:n0012 */ { error: /* ir:node:n0013 */ "not_found" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:n0014 */ { ok: /* ir:node:n0015 */ user };
        })());
  })();
}

export function lookupUser07(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:n0001 */ (() => {
    const trimmed: string = /* ir:node:n0002 */ (/* ir:node:n0003 */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:n0004 */ (/* ir:node:n0005 */ (/* ir:node:n0006 */ trimmed).length === 0)
      ? (/* ir:node:n0007 */ { error: /* ir:node:n0008 */ "invalid_user_id" })
      : (/* ir:node:n0009 */ (() => {
          const __semantic_ir_option_1 = /* ir:node:n0010 */ capabilities.users.getById(/* ir:node:n0011 */ trimmed);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:n0012 */ { error: /* ir:node:n0013 */ "not_found" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:n0014 */ { ok: /* ir:node:n0015 */ user };
        })());
  })();
}

export function lookupUser08(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:n0001 */ (() => {
    const trimmed: string = /* ir:node:n0002 */ (/* ir:node:n0003 */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:n0004 */ (/* ir:node:n0005 */ (/* ir:node:n0006 */ trimmed).length === 0)
      ? (/* ir:node:n0007 */ { error: /* ir:node:n0008 */ "invalid_user_id" })
      : (/* ir:node:n0009 */ (() => {
          const __semantic_ir_option_1 = /* ir:node:n0010 */ capabilities.users.getById(/* ir:node:n0011 */ trimmed);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:n0012 */ { error: /* ir:node:n0013 */ "not_found" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:n0014 */ { ok: /* ir:node:n0015 */ user };
        })());
  })();
}

export function lookupUser09(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:n0001 */ (() => {
    const trimmed: string = /* ir:node:n0002 */ (/* ir:node:n0003 */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:n0004 */ (/* ir:node:n0005 */ (/* ir:node:n0006 */ trimmed).length === 0)
      ? (/* ir:node:n0007 */ { error: /* ir:node:n0008 */ "invalid_user_id" })
      : (/* ir:node:n0009 */ (() => {
          const __semantic_ir_option_1 = /* ir:node:n0010 */ capabilities.users.getById(/* ir:node:n0011 */ trimmed);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:n0012 */ { error: /* ir:node:n0013 */ "not_found" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:n0014 */ { ok: /* ir:node:n0015 */ user };
        })());
  })();
}

export function lookupUser10(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:n0001 */ (() => {
    const trimmed: string = /* ir:node:n0002 */ (/* ir:node:n0003 */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:n0004 */ (/* ir:node:n0005 */ (/* ir:node:n0006 */ trimmed).length === 0)
      ? (/* ir:node:n0007 */ { error: /* ir:node:n0008 */ "invalid_user_id" })
      : (/* ir:node:n0009 */ (() => {
          const __semantic_ir_option_1 = /* ir:node:n0010 */ capabilities.users.getById(/* ir:node:n0011 */ trimmed);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:n0012 */ { error: /* ir:node:n0013 */ "not_found" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:n0014 */ { ok: /* ir:node:n0015 */ user };
        })());
  })();
}

export function lookupUser11(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:n0001 */ (() => {
    const trimmed: string = /* ir:node:n0002 */ (/* ir:node:n0003 */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:n0004 */ (/* ir:node:n0005 */ (/* ir:node:n0006 */ trimmed).length === 0)
      ? (/* ir:node:n0007 */ { error: /* ir:node:n0008 */ "invalid_user_id" })
      : (/* ir:node:n0009 */ (() => {
          const __semantic_ir_option_1 = /* ir:node:n0010 */ capabilities.users.getById(/* ir:node:n0011 */ trimmed);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:n0012 */ { error: /* ir:node:n0013 */ "not_found" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:n0014 */ { ok: /* ir:node:n0015 */ user };
        })());
  })();
}

export function lookupUser12(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:n0001 */ (() => {
    const trimmed: string = /* ir:node:n0002 */ (/* ir:node:n0003 */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:n0004 */ (/* ir:node:n0005 */ (/* ir:node:n0006 */ trimmed).length === 0)
      ? (/* ir:node:n0007 */ { error: /* ir:node:n0008 */ "invalid_user_id" })
      : (/* ir:node:n0009 */ (() => {
          const __semantic_ir_option_1 = /* ir:node:n0010 */ capabilities.users.getById(/* ir:node:n0011 */ trimmed);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:n0012 */ { error: /* ir:node:n0013 */ "not_found" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:n0014 */ { ok: /* ir:node:n0015 */ user };
        })());
  })();
}

export function lookupUser13(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:n0001 */ (() => {
    const trimmed: string = /* ir:node:n0002 */ (/* ir:node:n0003 */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:n0004 */ (/* ir:node:n0005 */ (/* ir:node:n0006 */ trimmed).length === 0)
      ? (/* ir:node:n0007 */ { error: /* ir:node:n0008 */ "invalid_user_id" })
      : (/* ir:node:n0009 */ (() => {
          const __semantic_ir_option_1 = /* ir:node:n0010 */ capabilities.users.getById(/* ir:node:n0011 */ trimmed);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:n0012 */ { error: /* ir:node:n0013 */ "not_found" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:n0014 */ { ok: /* ir:node:n0015 */ user };
        })());
  })();
}

export function lookupUser14(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:n0001 */ (() => {
    const trimmed: string = /* ir:node:n0002 */ (/* ir:node:n0003 */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:n0004 */ (/* ir:node:n0005 */ (/* ir:node:n0006 */ trimmed).length === 0)
      ? (/* ir:node:n0007 */ { error: /* ir:node:n0008 */ "invalid_user_id" })
      : (/* ir:node:n0009 */ (() => {
          const __semantic_ir_option_1 = /* ir:node:n0010 */ capabilities.users.getById(/* ir:node:n0011 */ trimmed);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:n0012 */ { error: /* ir:node:n0013 */ "not_found" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:n0014 */ { ok: /* ir:node:n0015 */ user };
        })());
  })();
}

export function lookupUser15(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:n0001 */ (() => {
    const trimmed: string = /* ir:node:n0002 */ (/* ir:node:n0003 */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:n0004 */ (/* ir:node:n0005 */ (/* ir:node:n0006 */ trimmed).length === 0)
      ? (/* ir:node:n0007 */ { error: /* ir:node:n0008 */ "invalid_user_id" })
      : (/* ir:node:n0009 */ (() => {
          const __semantic_ir_option_1 = /* ir:node:n0010 */ capabilities.users.getById(/* ir:node:n0011 */ trimmed);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:n0012 */ { error: /* ir:node:n0013 */ "not_found" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:n0014 */ { ok: /* ir:node:n0015 */ user };
        })());
  })();
}

export function lookupUser16(
  rawId: string, capabilities: SemanticCapabilities
): Result<User, string> {
  return /* ir:node:n0001 */ (() => {
    const trimmed: string = /* ir:node:n0002 */ (/* ir:node:n0003 */ rawId).replace(/^[\t\n\v\f\r ]+|[\t\n\v\f\r ]+$/g, "");
    return /* ir:node:n0004 */ (/* ir:node:n0005 */ (/* ir:node:n0006 */ trimmed).length === 0)
      ? (/* ir:node:n0007 */ { error: /* ir:node:n0008 */ "invalid_user_id" })
      : (/* ir:node:n0009 */ (() => {
          const __semantic_ir_option_1 = /* ir:node:n0010 */ capabilities.users.getById(/* ir:node:n0011 */ trimmed);
          if (__semantic_ir_option_1 === undefined) {
            return /* ir:node:n0012 */ { error: /* ir:node:n0013 */ "not_found" };
          }
          const user: User = __semantic_ir_option_1;
          return /* ir:node:n0014 */ { ok: /* ir:node:n0015 */ user };
        })());
  })();
}
