# Discuss

This is a smart and responsive Flask web application that fetches and displays the latest tech news headlines using the NewsAPI while using artificial intelligence to anaylze, discuss and educate users about concepts in the tech space.

## Features

- **Real-time Tech News**: Fetches latest technology headlines from NewsAPI
- **Modern UI**: Beautiful, responsive design with gradient backgrounds and card layouts
- **Article Images**: Displays article thumbnails with fallback placeholders
- **Publication Details**: Shows source, publication date, and formatted timestamps
- **Error Handling**: Graceful handling of API failures and network issues
- **Mobile Responsive**: Optimized for all screen sizes
- **Loading States**: Visual feedback while fetching news
- Smart news analysis and discussions

## Screenshots

The app features a modern card-based layout with:
- Gradient background design
- Hover effects and animations
- Clean typography and spacing
- Mobile-first responsive design

## Prerequisites

- Python 3.7 or higher
- NewsAPI key (free at [newsapi.org](https://newsapi.org))

## Installation

1. **Clone or download the project**
   ```bash
   cd Tech-news
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your NewsAPI key (optional)**
   
   For production use, set your API key as an environment variable:
   ```bash
   # Windows
   set NEWS_API_KEY=your_actual_api_key_here
   
   # macOS/Linux
   export NEWS_API_KEY=your_actual_api_key_here
   ```
   
   Note: The app includes a demo API key for testing purposes.

## Usage

1. **Start the development server**
   ```bash
   python app.py
   ```

2. **Open your browser**
   
   Navigate to `http://localhost:5000`

3. **View the latest tech news**
   
   The app will automatically fetch and display the latest technology headlines.

## Project Structure

```
Tech-news/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
├── templates/
│   └── index.html        # Main HTML template
└── static/
    └── css/
        └── style.css     # Modern CSS styling
```

## Configuration

### Environment Variables

- `NEWS_API_KEY`: Your NewsAPI key (optional, demo key included)



## API Information

This app uses the [NewsAPI](https://newsapi.org) to fetch news articles. The free tier includes:
- 1,000 requests per day
- Access to headlines and articles
- Multiple categories and sources

## Error Handling

The app includes comprehensive error handling for:
- Network connectivity issues
- API rate limits
- Invalid API responses
- Missing article data

## Browser Support

- Chrome (recommended)
- Firefox
- Safari
- Edge
- Mobile browsers

## Contributing

Feel free to fork this project and submit pull requests for improvements:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Troubleshooting

### Common Issues

1. **No articles loading**
   - Check your internet connection
   - Verify the NewsAPI service is available
   - Check if you've exceeded the API rate limit

2. **Styling not loading**
   - Ensure the `static/css/style.css` file exists
   - Check browser console for any errors
   - Try hard refresh (Ctrl+F5)

3. **Port already in use**
   - Change the port in `app.py`: `app.run(debug=True, port=5001)`

### Getting Help

If you encounter any issues:
1. Check the console output for error messages
2. Verify all dependencies are installed correctly
3. Ensure you're using a supported Python version

---

**Built using Flask and NewsAPI**
