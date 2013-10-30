user_dir="/Users/`whoami`"
packages="${user_dir}/Library/Application Support/Sublime Text 2/Packages"
custom_packages="${user_dir}/env/sublime-packages"

if [ -d "$packages" ]; then
  if [ -L "$packages" ]; then
    echo "* unlink user settings file"
    unlink "$packages"
  else
    echo "* moving user settings file"
    mv "$packages" "$packages.original"
  fi
fi

echo "* settings symlink to user settings from environment"
ln -s "$custom_packages" "$packages"
