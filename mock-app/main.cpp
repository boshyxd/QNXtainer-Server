#include <cstdlib>
#include <iostream>

int main() {
  if (const char *data_dir = std::getenv("DATA_DIR"))
    std::cout << "Your DATA_DIR is: " << data_dir << '\n';
}
