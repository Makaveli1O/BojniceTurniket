#!/usr/bin/env bash
set -euo pipefail

# ──────────────────────────────────────────────────────────────────────────────
# mraa installer (Debian/Ubuntu)
# - Builds from source, installs Python bindings + CLI tools
# - Optional: set MRAA_VERSION env var to checkout a specific tag/branch
#   e.g., MRAA_VERSION="v2.5.0"
# ──────────────────────────────────────────────────────────────────────────────

#--- sanity checks --------------------------------------------------------------
if ! command -v apt >/dev/null 2>&1; then
  echo "This script expects Debian/Ubuntu with apt. Exiting." >&2
  exit 1
fi

if [[ "$EUID" -ne 0 ]]; then
  echo "Please run as root (sudo ./install_mraa.sh)." >&2
  exit 1
fi

#--- settings -------------------------------------------------------------------
MRAA_REPO_URL="${MRAA_REPO_URL:-https://github.com/eclipse/mraa.git}"
MRAA_VERSION="${MRAA_VERSION:-}"         # empty = default branch
SRC_DIR="${SRC_DIR:-/usr/local/src/mraa}" # where to clone/build
BUILD_DIR="$SRC_DIR/build"
INSTALL_PREFIX="${INSTALL_PREFIX:-/usr}"  # install into /usr (recommended)

#--- deps -----------------------------------------------------------------------
echo ">>> Installing build dependencies…"
apt update
DEPS=(
  git cmake build-essential swig
  python3 python3-dev
  libjson-c-dev
)
apt install -y "${DEPS[@]}"

#--- fetch source ---------------------------------------------------------------
echo ">>> Fetching mraa sources…"
if [[ -d "$SRC_DIR/.git" ]]; then
  echo "mraa repo already present at $SRC_DIR — pulling latest…"
  git -C "$SRC_DIR" fetch --all --tags
else
  mkdir -p "$(dirname "$SRC_DIR")"
  git clone "$MRAA_REPO_URL" "$SRC_DIR"
fi

if [[ -n "$MRAA_VERSION" ]]; then
  echo ">>> Checking out $MRAA_VERSION"
  git -C "$SRC_DIR" checkout "$MRAA_VERSION"
else
  echo ">>> Using repository default branch"
  git -C "$SRC_DIR" checkout -q "$(git -C "$SRC_DIR" symbolic-ref --short HEAD)" || true
fi

#--- configure & build ----------------------------------------------------------
echo ">>> Configuring CMake…"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

cmake .. \
  -DBUILDSWIG=ON \
  -DBUILDSWIGPYTHON=ON \
  -DBUILDTOOLS=ON \
  -DCMAKE_INSTALL_PREFIX="$INSTALL_PREFIX"

echo ">>> Building…"
make -j"$(nproc)"

echo ">>> Installing…"
make install
ldconfig

#--- smoke tests ----------------------------------------------------------------
echo ">>> Smoke test: Python import"
if python3 - <<'PY'
import mraa
print("mraa Python OK — version:", mraa.getVersion())
PY
then
  echo "✓ Python import succeeded"
else
  echo "⚠ Python import failed. Check PYTHONPATH/site-packages locations." >&2
fi

echo ">>> Smoke test: CLI tools (mraa-gpio)"
if command -v mraa-gpio >/dev/null 2>&1; then
  echo "Available GPIOs (logical mapping):"
  mraa-gpio list || true
  echo "✓ mraa-gpio is installed"
else
  echo "⚠ mraa-gpio not found — tools may not have been built (BUILDTOOLS=ON needed)." >&2
fi

echo ">>> Done."
echo
echo "Next steps:"
echo "  • Verify your board’s logical pin numbers with:  mraa-gpio list"
echo "  • On some boards you may need to run your app with sudo to access GPIO."
echo "  • In Python, use: gpio = mraa.Gpio(<logical-pin>); gpio.dir(mraa.DIR_OUT); gpio.write(1)"

