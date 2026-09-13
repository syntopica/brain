on run argv
  set inPath to item 1 of argv
  set outPath to item 2 of argv
  tell application "Microsoft Word"
    set visible to false
    open POSIX file inPath
    set d to active document
    save as d file name outPath file format format PDF
    close d saving no
  end tell
end run
