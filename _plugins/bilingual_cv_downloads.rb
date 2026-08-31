# frozen_string_literal: true

require "cgi"

module BilingualCvDownloads
  module_function

  def render(page)
    downloads = page.data["cv_downloads"]
    return if downloads.nil?

    unless downloads.is_a?(Array) && !downloads.empty?
      raise Jekyll::Errors::FatalException, "cv_downloads must be a non-empty list"
    end

    links = downloads.map do |download|
      unless download.is_a?(Hash) && download["label"] && download["path"]
        raise Jekyll::Errors::FatalException, "each cv_downloads entry must define label and path"
      end

      label = CGI.escapeHTML(download["label"].to_s)
      href = relative_path(page, download["path"])
      language = download["lang"] ? %( lang="#{CGI.escapeHTML(download["lang"].to_s)}") : ""

      <<~HTML.chomp
        <a class="btn btn-sm btn-outline-primary" href="#{CGI.escapeHTML(href)}" target="_blank" rel="noopener noreferrer"#{language}>
          <i class="fa-solid fa-file-pdf" aria-hidden="true"></i>
          <span>#{label}</span>
        </a>
      HTML
    end

    heading_start = page.output.index('<h1 class="post-title">')
    heading_end = heading_start && page.output.index("</h1>", heading_start)
    unless heading_end
      raise Jekyll::Errors::FatalException, "CV download buttons could not find the CV page title"
    end

    actions = <<~HTML
      <span class="cv-download-actions" role="group" aria-label="CV downloads">
        #{links.join("\n")}
      </span>
    HTML
    page.output.insert(heading_end, actions)
  end

  def relative_path(page, path)
    path = path.to_s
    return path if path.match?(%r{\Ahttps?://})

    normalized_path = path.start_with?("/") ? path : "/#{path}"
    baseurl = page.site.config["baseurl"].to_s.sub(%r{/\z}, "")
    "#{baseurl}#{normalized_path}"
  end
end

Jekyll::Hooks.register :pages, :post_render do |page|
  next unless page.data["layout"] == "cv"

  BilingualCvDownloads.render(page)
end
